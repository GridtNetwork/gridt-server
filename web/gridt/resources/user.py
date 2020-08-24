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

        if not current_app.config["EMAIL_API_KEY"]:
            return ({"message": "Could not send e-mail: API key not available."}, 500)


class ResetPasswordResource(Resource):
    schema = ResetPasswordSchema()

    def post(self):

        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return ({"message": f"{field}: {error.messages[field][0]}"}, 400)
        
        if not res["password"] == res["password2"]:
            return ({"message": "Passwords do not match."}, 400)

        if 
            
