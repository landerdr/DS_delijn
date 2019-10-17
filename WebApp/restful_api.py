from flask_restful import Resource
from dl_requests import dl_request

class Test(Resource):
    def get(self):
        return dl_request().get("/gemeenten/57/haltes")

