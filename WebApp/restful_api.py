from flask_restful import Resource
from dl_requests import dl_request

# @https://data.delijn.be/docs/services/KernOpenDataServicesV1/operations/geefLijnen?
class GetAllLines(Resource):
    def get(self):
        return dl_request().get("/lijnen")

class GetLineInfo(Resource):
    def get(self, entiteitnummer, lijnnummer):
        return dl_request().get("/lijnen/%d/%d" %(entiteitnummer, lijnnummer))

class GetHandledStops(Resource):
    def get(self, entiteitnummer, lijnnummer, richting):
        if richting == "FIND":
            richting = GetEntityDirection().get(entiteitnummer, lijnnummer)["lijnrichtingen"][0]["richting"]
        haltes = dl_request().get("/lijnen/%d/%d/lijnrichtingen/%s/haltes" %(entiteitnummer, lijnnummer, richting))["haltes"]
        sorted_haltes = sorted(haltes, key=lambda k: k["geoCoordinaat"]["latitude"] + k["geoCoordinaat"]["longitude"])
        return {"haltes": sorted_haltes}

class GetEntityDirection(Resource):
    def get(self, entiteitnummer, lijnnummer):
        return dl_request().get("/lijnen/%d/%d/lijnrichtingen" %(entiteitnummer, lijnnummer))

class GetEntityStops(Resource):
    def get(self, entiteitnummer):
        return dl_request().get("/entiteiten/%d/haltes" %(entiteitnummer))


# @https://data.delijn.be/docs/services/KernOpenDataServicesV1/operations/geefRouteplan?
# https://api.delijn.be/DLKernOpenData/api/v1/routeplan/{vertrekLatlng}/{bestemmingLatlng}[?aanvraagType][&tijdstip][&vertrekAankomst][&vervoersOptie]

# https://api.delijn.be/DLKernOpenData/api/v1/lijnen/{entiteitnummer}/{lijnnummer}/lijnrichtingen/{richting}/real-time