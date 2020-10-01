"""
Login endpoint
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from .helpers import schema_loader
from gridt.schemas import LoginSchema

from gridt.models import User


class LoginResource(Resource):
    schema = LoginSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())
        user = User.find_by_email(data["username"])
        if user and user.verify_password(data["password"]):
            return {"access_token": create_access_token(identity=user.id)}, 200
        return {"message": "Credentials invalid"}, 401
