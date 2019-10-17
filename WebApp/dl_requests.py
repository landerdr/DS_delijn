import requests
# import xmltodict
from flask import json

class dl_request():
    def __init__(self):
        self.header = {"Ocp-Apim-Subscription-Key": "16dc01a8d7374c239ee2fb185689fb60"}
        self.baseurl = "https://api.delijn.be/DLKernOpenData/api/v1"
    
    def get(self, url):
        return json.loads(requests.get(self.baseurl + url, headers=self.header).content)
    
    def post(self, url, data):
        return json.loads(requests.put(self.baseurl + url, data, headers=self.header).content)

# class open_maps_request():
#     def __init__(self):
#         self.baseurl = "https://api.openstreetmap.org/"
    
#     def get(self, url):
#         o = xmltodict.parse(requests.get(self.baseurl + url).content)
#         return json.dumps(o)
    
#     def post(self, url, data):
#         o = xmltodict.parse(requests.put(self.baseurl + url, data).content)
#         return json.dumps(o)