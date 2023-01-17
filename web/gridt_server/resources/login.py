"""
Login endpoint
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import create_access_token
from .helpers import schema_loader
from gridt_server.schemas import LoginSchema

from gridtlib.controllers.user import verify_password_for_email
from sqlalchemy.exc import NoResultFound


class LoginResource(Resource):
    schema = LoginSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())

        try:
            user_id = verify_password_for_email(data["username"], data["password"])
            return {"access_token": create_access_token(identity=user_id)}
        except (ValueError, NoResultFound):
            return {"message": "Credentials invalid"}, 401
