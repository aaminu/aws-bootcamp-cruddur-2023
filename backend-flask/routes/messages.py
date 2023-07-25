from flask import request
from flask_cors import cross_origin

from lib.helpers import model_json

from aws_xray_sdk.core import xray_recorder

from services.message_groups import MessageGroups
from services.messages import Messages
from services.create_message import CreateMessage

def load(app):
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
