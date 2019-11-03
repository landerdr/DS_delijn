from flask import json
from flask_restful import Resource, reqparse, abort
from dl_requests import dl_request, open_maps_request, open_weather_requests
from utils import init_loading, progress_loading, complete_loading
import re
import datetime
import numpy as np

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
            progress_loading(i, len(args)//10)
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
init_loading()
cache["all_lines"] = GetAllLines()._getLines()
complete_loading()
cache["stops"] = {}
cache["lines"] = {}
# cache["schedules"] = {}
print("Done caching!")

# def GetSchedule(entiteitnummer, lijnnummer, richting):
#     key = "%d_%d_%s" %(int(entiteitnummer), int(lijnnummer), richting)
#     if key in cache["schedules"]:
#         return cache["schedules"][key]

#     return dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/dienstregelingen" %(int(entiteitnummer), int(lijnnummer), richting))




# class test(Resource):
#     def get(self, entiteitnummer, lijnnummer, richting):
#         response = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/dienstregelingen" %(entiteitnummer, lijnnummer, richting))
#         if response is not None:
#             return response
#         return None, 204

# class test2(Resource):
#     def get(self, entiteitnummer, lijnnummer, richting):
#         response = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/real-time" %(entiteitnummer, lijnnummer, richting))
#         if response is not None:
#             return response
#         return None, 204

class GetLineInfo(Resource):
    def get(self, entiteitnummer, lijnnummer):
        response = dl_request().get("/lijnen/%d/%d" % (entiteitnummer, lijnnummer))
        if response is not None:
            return response
        return None, 204

class GetHandledStops(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        o = GetRealtimeInfo()
        s, _ = o._get_stops(entiteitnummer, lijnnummer, richting)
        if s is not None:
            return {"haltes": o.haltes}
        return None, 204

class GetStopInformation(Resource):
    def get(self, entiteitnummer, haltenummer):
        key = "%s_%s" %(entiteitnummer, haltenummer)
        halte = {}
        if key in cache["stops"]:
            halte = cache["stops"][key]
        else:
            halte = dl_request().get("/haltes/%d/%d" %(int(entiteitnummer), int(haltenummer)))
            if halte is None:
                return None
            halte.pop("links")
            cache["stops"][key] = halte

        halte["weather"] = GetRealtimeInfo()._get_weather(halte["geoCoordinaat"]["latitude"], halte["geoCoordinaat"]["longitude"])

        return halte


class GetBusUpdate(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        o = GetRealtimeInfo()
        s, _ = o._get_bus_locations(entiteitnummer, lijnnummer, richting)
        if s is None:
            return None, 204
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
            # If you want weather information from main api call
            # if len(self.haltes) > 60:
            #     halte["weather"] = {"message": "Invalid amount of stops, max amount of 60 (openweathermap limitation)"}
            # else:
            #     halte["weather"] = self._get_weather(halte["geoCoordinaat"]["latitude"], halte["geoCoordinaat"]["longitude"])

        return True, 200

    def _find_stops(self, data, entiteitnummer, lijnnummer, richting):
        # Create unique line key
        key = "%d_%d_%s" %(int(entiteitnummer), int(lijnnummer), richting)
        # Create chache of ordered stops
        if key not in cache["lines"] or (key in cache["lines"] and len(data["doorkomsten"]) > len(cache["lines"][key])):
            stops = []
            for stop in data["doorkomsten"]:
                ent = int(re.split("/", stop["links"][0]["url"])[-2])
                stops.append((ent, stop["haltenummer"]))
            cache["lines"][key] = stops

        # Search for stops
        w_cur = None
        w_prev = None
        time = None
        prev = None
        for waypoint in data["doorkomsten"]:
            if "dienstregelingTijdstip" in waypoint:
                w_cur = waypoint
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
            ent = int(re.split("/", w_prev["links"][0]["url"])[-2])
            geo = GetStopInformation().get(ent, w_prev["haltenummer"])["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(prev)
            # Stop 2
            ent = int(re.split("/", w_cur["links"][0]["url"])[-2])
            geo = GetStopInformation().get(ent, w_cur["haltenummer"])["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(time)
            return response
        elif w_cur is not None:
            # Looks for prev stop in cache
            ent = int(re.split("/", w_cur["links"][0]["url"])[-2])
            for stop in cache["lines"][key]:
                if stop[0] == ent and stop[1] == w_cur["haltenummer"]:
                    break
                w_prev = stop
            # If none gets found, return next stop
            if w_prev is None or time < datetime.datetime.now() or w_prev == cache["lines"][key][-1]:
                geo = GetStopInformation().get(ent, w_cur["haltenummer"])["geoCoordinaat"]
                return [[geo["longitude"], geo["latitude"]]]
            # Return both stops
            response = [[], []]
            # Looked up stop 1
            geo = GetStopInformation().get(w_prev[0], w_prev[1])["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(datetime.datetime.now() - datetime.timedelta(minutes=1))
            # Stop 2
            geo = GetStopInformation().get(ent, w_cur["haltenummer"])["geoCoordinaat"]
            response[0].append([geo["longitude"], geo["latitude"]])
            response[1].append(time)
            return response
        else:
            return None

    def _get_routing(self, waypoints):
        return open_maps_request().post("/v2/directions/driving-car/geojson", {"coordinates": waypoints})

    def _get_bus_locations(self, entiteitnummer, lijnnummer, richting):
        self.busses = []
        # Request real-time data from DL
        real_time_data = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/real-time" % (entiteitnummer, lijnnummer, richting))
        if real_time_data is None:
            return None, 204
        # Test reasons
        self.test = real_time_data
        # Sort busses so the one with the most stops gets handled first
        busses = sorted(real_time_data["ritDoorkomsten"], key=lambda k: len(k["doorkomsten"]), reverse=True)
        for bus in busses:
            waypoints = self._find_stops(bus, entiteitnummer, lijnnummer, richting)
            if waypoints is not None:
                if len(waypoints) == 1:
                    self.busses.append({"ritnummer": bus["ritnummer"], "geoCoordinaat": {"longitude": waypoints[0][0], "latitude": waypoints[0][1]}})
                else:
                    # Requests routing
                    response = self._get_routing(waypoints[0])
                    if response is None:
                        return None, 204
                    route = json.loads(response)
                    

                    # Calculate percentage traveled by time
                    if waypoints[1][1] == waypoints[1][0]:
                        perc = 1
                    else:
                        delta = waypoints[1][1] - waypoints[1][0]
                        perc = min((datetime.datetime.now() - waypoints[1][0])/delta, 1)

                    # Calculate euclidean distance between points
                    coordinates = route["features"][0]["geometry"]["coordinates"]
                    coor_dist = []
                    for i in range(1, len(coordinates)):
                        coor_dist.append(np.sqrt(np.square(coordinates[i-1][0] - coordinates[i][0]) + np.square(coordinates[i-1][1] - coordinates[i][1])))

                    # Finds coordinates for route
                    distance = perc * np.sum(coor_dist)
                    point1 = None
                    point2 = None
                    for i in range(len(coor_dist)):
                        distance -= coor_dist[i]
                        if distance <= 0:
                            perc = (distance + coor_dist[i]) / coor_dist[i]
                            point1 = coordinates[i]
                            point2 = coordinates[i+1]
                            break

                    lon1 = point1[0]
                    lat1 = point1[1]
                    lon2 = point2[0]
                    lat2 = point2[1]

                    delta_lon = perc * (lon2 - lon1)
                    delta_lat = perc * (lat2 - lat1)

                    self.busses.append({"ritnummer": bus["ritnummer"], "geoCoordinaat": {"longitude": lon1 + delta_lon, "latitude": lat1 + delta_lat}, "geo": coordinates})
        return True, 200


    def get(self, entiteitnummer, lijnnummer, richting):
        s, _ = self._get_stops(entiteitnummer, lijnnummer, richting)
        if s is None:
            return None, 204
        s, _ = self._get_bus_locations(entiteitnummer, lijnnummer, richting)
        if s is None:
            return None, 204
        return {"haltes": self.haltes, "busses": self.busses, "test": self.test}

class GetRoute(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        sorted_haltes = GetHandledStops().get(entiteitnummer, lijnnummer, richting)["haltes"]
        return open_maps_request().post("/v2/directions/driving-car/geojson", {"coordinates": sorted_haltes})
