from flask import json
from flask_restful import Resource, reqparse, abort
from dl_requests import dl_request, open_maps_request, open_weather_requests
import re
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
            public_line[key] = {"lijnnummerPubliek": line["lijnnummerPubliek"], "vervoertype": line["vervoertype"]}
            args.append(key)

        for i in range(0, (len(args)//10) + 1):
            all_data = dl_request().get("/lijnen/lijst/%s/lijnrichtingen" %
                                        ("_".join(args[10*i:min(10*(i+1), len(args))])))
            for lines in all_data["lijnLijnrichtingen"]:
                for line in lines["lijnrichtingen"]:
                    key = "%s_%s" % (
                        line["entiteitnummer"], line["lijnnummer"])
                    line["lijnnummerPubliek"] = public_line[key]["lijnnummerPubliek"]
                    line["vervoertype"] = public_line[key]["vervoertype"]
                    line.pop("links")
                    response["lijnen"].append(line)

        return response

    def get(self):
        return cache["all_lines"]

print("Start caching all lines")
cache["all_lines"] = GetAllLines()._getLines()
cache["stops"] = {}
cache["schedules"] = {}
print("Done caching!")

def GetSchedule(entiteitnummer, lijnnummer, richting):
    key = "%d_%d_%s" %(int(entiteitnummer), int(lijnnummer), richting)
    if key in cache["schedules"]:
        return cache["schedules"][key]
    
    response = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/dienstregelingen" %(int(entiteitnummer), int(lijnnummer), richting))
    if response is None:
        return None, 204
    


class test(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        response = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/dienstregelingen" %(entiteitnummer, lijnnummer, richting))
        if response is not None:
            return response
        return None, 204

class test2(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        response = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/real-time" %(entiteitnummer, lijnnummer, richting))
        if response is not None:
            return response
        return None, 204

class GetLineInfo(Resource):
    def get(self, entiteitnummer, lijnnummer):
        response = dl_request().get("/lijnen/%d/%d" % (entiteitnummer, lijnnummer))
        if response is not None:
            return response
        return None, 204

class GetHandledStops(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        haltes = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/haltes" %
                                  (entiteitnummer, lijnnummer, richting))["haltes"]

        for halte in haltes:
            halte.pop("links")
            halte.pop("gemeentenummer")

        return {"haltes": haltes}

class GetStopInformation(Resource):
    def get(self, entiteitnummer, haltenummer):
        key = "%s_%s" %(entiteitnummer, haltenummer)
        halte = {}
        if key in cache["stops"]:
            halte = cache["stops"][key]
        else:
            halte = dl_request().get("/haltes/%d/%d" %(int(entiteitnummer), int(haltenummer)))
            if halte is None:
                return halte
            halte.pop("links")
            cache["stops"][key] = halte

        halte["weather"] = GetRealtimeInfo()._get_weather(halte["geoCoordinaat"]["latitude"], halte["geoCoordinaat"]["longitude"])

        return halte


class GetBusUpdate(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        o = GetRealtimeInfo()
        o._get_bus_locations(entiteitnummer, lijnnummer, richting)
        return {"busses": o.busses}



class GetRealtimeInfo(Resource):
    def _get_weather(self, lat, lon):
        return open_weather_requests().get("/weather?lat=%s&lon=%s" %(lat, lon))

    def _get_stops(self, entiteitnummer, lijnnummer, richting): 
        response = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/haltes" %
                                  (entiteitnummer, lijnnummer, richting))
        if response is None:
            return None, 204
        self.haltes = response["haltes"]
        for halte in self.haltes:
            halte.pop("links")
            key = "%s_%s" %(halte["entiteitnummer"], halte["haltenummer"])
            if key not in cache["stops"]:
                cache["stops"][key] = halte            

    def _find_stops(self, data):
        w_cur = None
        w_prev = None
        time = None
        prev = None
        for waypoint in data["doorkomsten"]:
            w_cur = waypoint
            if "dienstregelingTijdstip" in waypoint:
                if "real-timeTijdstip" in waypoint:
                    time = datetime.datetime.strptime(waypoint["real-timeTijdstip"], "%Y-%m-%dT%H:%M:%S")
                else:
                    time = datetime.datetime.strptime(waypoint["dienstregelingTijdstip"], "%Y-%m-%dT%H:%M:%S")
                if time > datetime.datetime.now():
                    break
                prev = time
                w_prev = waypoint

        if w_prev is not None and w_prev["haltenummer"] != w_cur["haltenummer"]:
            response = [[], []]
            # Stop 1
            entiteitnummer = int(re.split("/", w_prev["links"][0]["url"])[-2])
            geo = GetStopInformation().get(entiteitnummer, w_prev["haltenummer"])["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(prev)
            # Stop 2
            entiteitnummer = int(re.split("/", w_cur["links"][0]["url"])[-2])
            geo = GetStopInformation().get(entiteitnummer, w_cur["haltenummer"])["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(time)
            return response
        elif w_cur is not None:
            entiteitnummer = int(re.split("/", w_cur["links"][0]["url"])[-2])
            geo = GetStopInformation().get(entiteitnummer, w_cur["haltenummer"])["geoCoordinaat"]
            return [[geo["longitude"], geo["latitude"]]]
        else:
            return None
    
    def _get_routing(self, waypoints):
        return open_maps_request().post("/v2/directions/driving-car/geojson", {"coordinates": waypoints})

    def _get_bus_locations(self, entiteitnummer, lijnnummer, richting):
        self.busses = []
        real_time_data = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/real-time" % (entiteitnummer, lijnnummer, richting))
        self.test = real_time_data
        for bus in real_time_data["ritDoorkomsten"]:
            waypoints = self._find_stops(bus)
            if waypoints is not None:
                if len(waypoints) == 1:
                    self.busses.append({"ritnummer": bus["ritnummer"], "geoCoordinaat": {"longitude": waypoints[0][0], "latitude": waypoints[0][1]}})
                else:
                    # lon1 = waypoints[0][0][0]
                    # lat1 = waypoints[0][0][1]
                    # lon2 = waypoints[0][1][0]
                    # lat2 = waypoints[0][1][1]

                    route = json.loads(self._get_routing(waypoints[0]))
                    routing = route["features"][0]["properties"]["segments"][0]

                    delta = waypoints[1][1] - waypoints[1][0]
                    if delta == 0:
                        perc = 1
                    else:
                        perc = (datetime.datetime.now() - waypoints[1][0])/delta
                    distance = perc * routing["distance"]
                    way_points = None
                    for segment in routing["steps"]:
                        distance -= segment["distance"]
                        if distance <= 0:
                            perc = (segment["distance"] + distance) / segment["distance"]
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

                    self.busses.append({"ritnummer": bus["ritnummer"], "geoCoordinaat": {"longitude": lon1 + delta_lon, "latitude": lat1 + delta_lat}})


    def get(self, entiteitnummer, lijnnummer, richting):
        self._get_stops(entiteitnummer, lijnnummer, richting)
        self._get_bus_locations(entiteitnummer, lijnnummer, richting)
        return {"haltes": self.haltes, "busses": self.busses, "test": self.test}

class GetRoute(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        sorted_haltes = GetHandledStops().get(entiteitnummer, lijnnummer, richting)["haltes"]
        return open_maps_request().post("/v2/directions/driving-car/geojson", {"coordinates": sorted_haltes})
