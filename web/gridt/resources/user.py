from flask import request, current_app
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from marshmallow import ValidationError

from passlib.apps import custom_app_context as pwd_context

from gridt.models.user import User
from gridt.schemas import (
    BioSchema,
    ChangeEmailSchema
    ChangePasswordSchema,
    RequestPasswordResetSchema,
    ResetPasswordSchema,
)

from gridt.db import db
import jwt
from util.email_templates import (
    send_password_reset_email,
    send_password_change_notification,
)


class BioResource(Resource):
    @jwt_required()
    def put(self):
        schema = BioSchema()

        data = request.get_json()
        bio = None
        try:
            bio = schema.load(data)["bio"]
        except ValidationError as error:
            return {"message": "Bad request."}, 400

        current_identity.bio = bio
        current_identity.save_to_db()

        return {"message": "Bio successfully changed."}


class ChangePasswordResource(Resource):
    schema = ChangePasswordSchema()

    @jwt_required()
    def post(self):
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)

        if not current_identity.verify_password(res["old_password"]):
            return ({"message": "Failed to identify user with given password."}, 400)

        if current_identity.verify_password(res["old_password"]):
            current_identity.hash_and_store_password(res["new_password"])

            send_password_change_notification(current_identity.email)
            return ({"message": "Successfully changed password."}, 200)


class ChangeEmailResource(Resource):
    schema = ChangeEmailSchema()

    @jwt_required()
    def post(self):
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)
        
        if not current_identity.verify_password(res["password"]):
            return ({"message": "Failed to identify user with given password."}, 400)

        if current_identity.verify_password(res["password"]):
            current_identity.email = res["new_email"]
            return ({"message": "Successfully changed email."}, 200)


class RequestPasswordResetResource(Resource):
    schema = RequestPasswordResetSchema()
    
    def post(self):
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)
        if not current_app.config["EMAIL_API_KEY"]:
            return ({"message": "Could not send e-mail; API key not available."}, 500)

        user = User.find_by_email(res["email"])
        if not user:
            # We don't want malicious users to know whether or not an e-mail is in our database.
            return ({"message": "Recovery e-mail successfully sent."}, 200)

        token = user.get_password_reset_token()
        send_password_reset_email(user.email, token)
        return ({"message": "Recovery e-mail successfully sent."}, 200)


class ResetPasswordResource(Resource):
    schema = ResetPasswordSchema()

    def post(self):
        secret_key = current_app.config["SECRET_KEY"]
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)

        token_decoded = jwt.decode(res["token"], secret_key, algorithms=["HS256"])
        user_id = token_decoded["user_id"]
        password = res["password"]

        user = User.find_by_id(user_id)
        user.hash_and_store_password(password)

        send_password_change_notification(user.email)
        return ({"message": "Successfully changed password."}, 200)