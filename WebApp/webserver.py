from flask import Flask, Blueprint, render_template, jsonify, session, request, redirect, json, abort, send_from_directory
from flask_restful import reqparse, abort, Api, Resource
import restful_api

app = Flask(__name__)
api = Api(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "abcdefgsecretkey123420"
app_data = dict()

## Custom error ##
@app.errorhandler(404)
def render_404(errormsg):
    return errormsg

@app.errorhandler(401)
def render_401(errormsg):
    return errormsg

@app.route("/")
def home():
    return render_template("home.html")

api.add_resource(restful_api.Test, "/api/1")
api.add_resource(restful_api.Test2, "/api/2")

if __name__ == "__main__":
    app.env = "development"
    app.testing = True
    
    app.run(ssl_context="adhoc", port="5000")