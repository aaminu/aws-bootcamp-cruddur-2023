import os
import sys

from flask import Flask
from flask import request
from flask_cors import cross_origin

from lib.rollbar import init_rollbar
from lib.xray import init_xray
from lib.cors import init_cors
from lib.cloudwatch import init_cloudwatch
from lib.honeycomb import init_honeycomb
from lib.jwt_verify_middleware import JWTVerificationMiddleware, jwt_decoder

from services.home_activities import *
from services.notifications_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *
from services.users_short import *
from services.update_profile import *


app = Flask(__name__)

with app.app_context():
    rollbar = init_rollbar()
init_xray(app)
init_honeycomb(app)
init_cors(app)
# Wrap app with middleware
JWTVerificationMiddleware(app, jwt_decoder)

# Cloudwatch Logs
# @app.after_request
# def after_request(response):
#     init_cloudwatch(response)

def model_json(model):
    if model['errors'] is not None:
        return model['errors'], 422
    else:
        return model['data'], 200


@app.route('/rollbar/test')
def rollbar_test():
    rollbar.report_message('Hello World!', 'warning')
    return "Hello World!"

@app.route('/api/health-check')
def health_check():
    return {'success': True, 'ver': 1}, 200


@app.route("/api/message_groups", methods=['GET'])
def data_message_groups():
    claims = request.args.get("claims")
    cognito_user_id = claims.get("sub")

    model = MessageGroups.run(cognito_user_id=cognito_user_id)
    return model_json(model)


@app.route("/api/messages/<string:message_group_uuid>", methods=['GET'])
def data_messages(message_group_uuid):

    claims = request.args.get("claims")
    cognito_user_id = claims.get("sub")

    model = Messages.run(cognito_user_id=cognito_user_id,
                         message_group_uuid=message_group_uuid)
    return model_json(model)


@app.route("/api/messages", methods=['POST', 'OPTIONS'])
@cross_origin()
def data_create_message():
    message_group_uuid = request.json.get('message_group_uuid', None)
    user_receiver_handle = request.json.get('handle', None)
    message = request.json['message']
    app.logger.info("========user_receiver========: {}".format( user_receiver_handle))
    claims = request.args.get("claims")
    cognito_user_id = claims.get("sub")
   
    if message_group_uuid is not None:
        model = CreateMessage.run(
            "update",
            message=message,
            message_group_uuid=message_group_uuid,
            cognito_user_id=cognito_user_id,
            user_receiver_handle=user_receiver_handle)
    else:
        model = CreateMessage.run(
            "create",
            message=message,
            cognito_user_id=cognito_user_id,
            user_receiver_handle=user_receiver_handle)

    return model_json(model)


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


@app.route("/api/activities/@<string:handle>", methods=['GET'])
def data_handle(handle):
    model = UserActivities.run(handle)
    return model_json(model)


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


@app.route("/api/activities/<string:activity_uuid>", methods=['GET'])
def data_show_activity(activity_uuid):
    data = ShowActivities.run(activity_uuid=activity_uuid)
    return data, 200


@app.route("/api/activities/<string:activity_uuid>/reply", methods=['POST', 'OPTIONS'])
@cross_origin()
def data_activities_reply(activity_uuid):
    
    claims = request.args.get("claims")
    username = claims.get("username")
    message = request.json['message']
    app.logger.info(claims)
    model = CreateReply.run(message, username, activity_uuid)
    return model_json(model)


@app.route("/api/users/@<string:handle>/short", methods=['GET'])
def data_users_short(handle):
    data = UsersShort.run(handle)
    return data, 200


@app.route("/api/profile/update", methods=['POST','OPTIONS'])
@cross_origin()
def data_update_profile():
    bio          = request.json.get('bio',None)
    display_name = request.json.get('display_name',None)
    claims = request.args.get("claims")
    cognito_user_id = claims.get("sub")

    model = UpdateProfile.run(
        cognito_user_id=cognito_user_id, 
        bio=bio, 
        display_name=display_name
        )
    return model_json(model)


if __name__ == "__main__":
    app.run(debug=True)
