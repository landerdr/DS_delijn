from flask import json
from flask_restful import Resource, reqparse, abort
from dl_requests import dl_request, open_maps_request, open_weather_requests
import datetime

# @https://data.delijn.be/docs/services/KernOpenDataServicesV1/operations/geefLijnen

cache = {}

class GetAllLines(Resource):
    def _getLines(self):
        response = {"lijnen": []}
        args = []
        lines = dl_request().get("/lijnen")["lijnen"]
        public_line = {}
        for line in lines:
            key = "%s_%s" % (line["entiteitnummer"], line["lijnnummer"])
            public_line[key] = line["lijnnummerPubliek"]
            args.append(key)

        for i in range(0, (len(args)//10) + 1):
            all_data = dl_request().get("/lijnen/lijst/%s/lijnrichtingen" %
                                        ("_".join(args[10*i:min(10*(i+1), len(args))])))
            for lines in all_data["lijnLijnrichtingen"]:
                for line in lines["lijnrichtingen"]:
                    key = "%s_%s" % (
                        line["entiteitnummer"], line["lijnnummer"])
                    line["lijnnummerPubliek"] = public_line[key]
                    line.pop("links")
                    response["lijnen"].append(line)

        return response

    def get(self):
        return cache["all_lines"]

cache["all_lines"] = GetAllLines()._getLines()




class GetLineInfo(Resource):
    def get(self, entiteitnummer, lijnnummer):
        return dl_request().get("/lijnen/%d/%d" % (entiteitnummer, lijnnummer))

class GetHandledStops(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        haltes = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/haltes" %
                                  (entiteitnummer, lijnnummer, richting))["haltes"]

        for halte in haltes:
            halte.pop("links")
            halte.pop("gemeentenummer")

        return {"haltes": haltes}


class GetRealtimeInfo(Resource):
    def _get_weather(self, lon, lat):
        return open_weather_requests().get("/weather?lat=%s&lon=%s" %(lat, lon))

    def _get_stops(self, entiteitnummer, lijnnummer, richting):
        self.data = {}
        self.haltes = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/haltes" %
                                  (entiteitnummer, lijnnummer, richting))["haltes"]

        for halte in self.haltes:
            halte.pop("links")
            halte.pop("gemeentenummer")
            # halte["weather"] = self._get_weather(halte["geoCoordinaat"]["latitude"], halte["geoCoordinaat"]["longitude"])
            self.data[halte["haltenummer"]] = halte

    def _find_stops(self, data):
        i = 0
        time = None
        prev = None
        for waypoint in data["doorkomsten"]:
            time = datetime.datetime.strptime(waypoint["dienstregelingTijdstip"], "%Y-%m-%dT%H:%M:%S")
            if time >= datetime.datetime.now():
                break
            prev = time
            i += 1
        if i > 0 and i < len(data["doorkomsten"]):
            response = [[], []]
            # Stop 1
            geo = self.data[data["doorkomsten"][i-1]["haltenummer"]]["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(prev)
            # Stop 2
            geo = self.data[data["doorkomsten"][i]["haltenummer"]]["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(time)
            return response
        else:
            return None
    
    def _get_routing(self, waypoints):
        return open_maps_request().post("/v2/directions/driving-car/geojson", {"coordinates": waypoints})

    def _get_bus_locations(self, entiteitnummer, lijnnummer, richting):
        real_time_data = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/real-time" % (entiteitnummer, lijnnummer, richting))
        self.busses = []
        for bus in real_time_data["ritDoorkomsten"]:
            waypoints = self._find_stops(bus)
            if waypoints is not None:
                # lon1 = waypoints[0][0][0]
                # lat1 = waypoints[0][0][1]
                # lon2 = waypoints[0][1][0]
                # lat2 = waypoints[0][1][1]

                route = json.loads(self._get_routing(waypoints[0]))
                routing = route["features"][0]["properties"]["segments"][0]

                delta = waypoints[1][1] - waypoints[1][0]
                perc = (datetime.datetime.now() - waypoints[1][0])/delta
                distance = perc * routing["distance"]
                way_points = None
                for segment in routing["steps"]:
                    distance -= segment["distance"]
                    if distance <= 0:
                        way_points = segment["way_points"]
                        break

                routing = route["features"][0]
                point1 = routing["geometry"]["coordinates"][int(way_points[0])]
                point2 = routing["geometry"]["coordinates"][int(way_points[1])]

                lon1 = point1[0]
                lat1 = point1[1]
                lon2 = point2[0]
                lat2 = point2[1]

                delta_lon = perc * (lon2 - lon1)
                delta_lat = perc * (lat2 - lat1)

                self.busses.append({"ritnummer": bus["ritnummer"], "geoCoordinaat": [lon1 + delta_lon, lat1 + delta_lat]})


    def get(self, entiteitnummer, lijnnummer, richting):
        self._get_stops(entiteitnummer, lijnnummer, richting)
        self._get_bus_locations(entiteitnummer, lijnnummer, richting)
        return {"haltes": self.haltes, "busses": self.busses}

class GetRoute(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        sorted_haltes = GetHandledStops().get(entiteitnummer, lijnnummer, richting)["haltes"]
        return open_maps_request().post("/v2/directions/driving-car/geojson", {"coordinates": sorted_haltes})
