from flask import request
from flask_cors import cross_origin

from lib.helpers import model_json

from aws_xray_sdk.core import xray_recorder

from services.home_activities import *
from services.notifications_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *

def load(app):
    @app.route("/api/activities/home", methods=['GET'])
    @cross_origin()
    def data_home():
        claims = request.args.get("claims")
        if claims.get("sub") is None:
            data = HomeActivities.run()
        else:
            data = HomeActivities.run(cognito_user=claims.get("username"))
        return data, 200

    @app.route("/api/activities/notifications", methods=['GET'])
    def data_notifications():
        data = NotificationsActivities.run()
        return data, 200

    @app.route("/api/activities/search", methods=['GET'])
    def data_search():
        term = request.args.get('term')
        model = SearchActivities.run(term)
        return model_json(model)

    @app.route("/api/activities", methods=['POST', 'OPTIONS'])
    @cross_origin()
    def data_activities():
        claims = request.args.get("claims")
        username = claims.get("username")
        message = request.json['message']
        ttl = request.json['ttl']
        model = CreateActivity.run(message, username, ttl)
        
        return model_json(model)

    @app.route("/api/activities/<string:activity_uuid>/reply", methods=['POST', 'OPTIONS'])
    @cross_origin()
    def data_activities_reply(activity_uuid):
        claims = request.args.get("claims")
        cognito_user_id = claims.get("sub")
        message = request.json['message']
        model = CreateReply.run(message, cognito_user_id, activity_uuid)
        return model_json(model)