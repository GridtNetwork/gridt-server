from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from .helpers import schema_loader
from gridt_server.schemas import NewUserSchema
from gridt.controllers.user import get_identity, register


class IdentityResource(Resource):
    @jwt_required
    def get(self):
        return get_identity(get_jwt_identity())


class RegisterResource(Resource):
    schema = NewUserSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())
        register(data["username"], data["email"], data["password"])
        return {"message": "Succesfully created user."}, 201
