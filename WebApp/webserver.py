from flask import Flask, Blueprint, render_template, jsonify, session, request, redirect, json, abort, send_from_directory
from flask_restful import Api
import restful_api

app = Flask(__name__)
api = Api(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "987654321123456789_help"
app_data = dict()

## Custom error ##
@app.errorhandler(404)
def render_404(errormsg):
    return errormsg

@app.errorhandler(401)
def render_401(errormsg):
    return errormsg

@app.route("/map")
def home():
    lines = restful_api.GetAllLines().get()
    return render_template("home.html", lines=lines)

@app.route("/")
def manual():
    return render_template("manual.html")

# Used for site
api.add_resource(restful_api.GetAllLines, "/api/all-lines")
api.add_resource(restful_api.GetStopInformation, "/api/stop/<int:entiteitnummer>/<int:haltenummer>")
api.add_resource(restful_api.GetRealtimeInfo, "/api/real-time/<int:entiteitnummer>/<int:lijnnummer>/<string:richting>")
api.add_resource(restful_api.GetBusUpdate, "/api/update/<int:entiteitnummer>/<int:lijnnummer>/<string:richting>")

# Legacy endpoints, used for testing
api.add_resource(restful_api.GetHandledStops, "/api/stops/<int:entiteitnummer>/<int:lijnnummer>/<string:richting>")
api.add_resource(restful_api.GetRoute, "/api/routing/<int:entiteitnummer>/<int:lijnnummer>/<string:richting>")
api.add_resource(restful_api.GetLineInfo, "/api/line/<int:entiteitnummer>/<int:lijnnummer>")

if __name__ == "__main__":
    app.env = "development"
    app.testing = True

    app.run(port="5000") # ssl_context="adhoc"
