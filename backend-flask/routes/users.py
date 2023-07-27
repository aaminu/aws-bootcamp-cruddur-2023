from flask import request
from flask_cors import cross_origin

from lib.helpers import model_json

from services.user_activities import UserActivities
from services.users_short import UsersShort
from services.update_profile import UpdateProfile
from services.show_activity import ShowActivity


def load(app):
    @app.route("/api/activities/@<string:handle>", methods=['GET'])
    @cross_origin()
    def data_users_activities(handle):
        model = UserActivities.run(handle)
        return model_json(model)

    @app.route("/api/users/@<string:handle>/short", methods=['GET'])
    @cross_origin()
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

    @app.route("/api/activities/@<string:handle>/status/<string:activity_uuid>", methods=['GET'])
    def data_show_activity(handle,activity_uuid):
        data = ShowActivity.run(activity_uuid)
        return data, 200