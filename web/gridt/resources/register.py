from flask import request
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from gridt.models.user import User
from gridt.schemas import NewUserSchema

from marshmallow import ValidationError


class LoggedInResource(Resource):
    @jwt_required()
    def get(self):
        return {
            "id": current_identity.id,
            "username": current_identity.username,
            "bio": current_identity.bio,
            "avatar": current_identity.email_hash,
        }, 200


class RegisterResource(Resource):
    def post(self):
        schema = NewUserSchema()

        data = None
        try:
            data = schema.load(request.get_json())
        except ValidationError:
            return {"message": "Bad request"}, 400

        user = User(data["username"], data["email"], data["password"])
        user.save_to_db()

        return {"message": "Succesfully created user."}, 201
