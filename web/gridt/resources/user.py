from flask import request, current_app
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from marshmallow import ValidationError

from passlib.apps import custom_app_context as pwd_context

from gridt.models.user import User
from gridt.schemas import (
    BioSchema, 
    ChangePasswordSchema,
    RequestPasswordResetSchema,
    ResetPasswordSchema
)

from gridt.db import db
import jwt
from util import send_email


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
            current_identity.hash_password(res["new_password"])
            return ({"message": "Successfully changed password."}, 200)


class RequestPasswordResetResource(Resource):
    schema = RequestPasswordResetSchema()
    
    def post(self):
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)
        
        # Currently does not do anything since EMAIL_API_KEY is in environment variables,
        # not in config.
        if not current_app.config["EMAIL_API_KEY"]:
            return ({"message": "Could not send e-mail: API key not available."}, 500)

        user = User.find_by_email(res["email"])
        token = user.get_password_reset_token()
        link = f"https://app.gridt.org/reset_password?token={token}"
        subj = "Reset your password"
        body = f"Your password has been reset, please follow the following link: {link}"
        send_email(user.email, subj, body)
        return ({"message": "Recovery email successfully sent."}, 200)


class ResetPasswordResource(Resource):
    schema = ResetPasswordSchema()
    
    def post(self):
        secret_key = current_app.config["SECRET_KEY"]
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)

        try:
            token_decoded = jwt.decode(res["token"], secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            msg = "Signature has expired."
            return ({"message": msg}, 400)
        except jwt.InvalidTokenError:
            msg = "Invalid token."
            return ({"message": msg}, 400)
        
        id = token_decoded["reset_password"]
        password = res["password"]
        user = User.query.get(id)
        user.hash_password(password)

        msg = "Password successfully changed."
        return ({"message": msg}, 200)