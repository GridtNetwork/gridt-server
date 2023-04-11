from flask import request, current_app
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from .helpers import schema_loader
from gridt_server.schemas import NewUserSchema
from gridt.controllers.user import get_identity, register


class IdentityResource(Resource):
    @jwt_required()
    def get(self):
        return get_identity(get_jwt_identity())


class RegisterResource(Resource):
    schema = NewUserSchema()

    def post(self):
        data = schema_loader(self.schema, request.get_json())

        request_admin_key = data.get("admin_key")
        has_key = request_admin_key is not None
        if has_key and request_admin_key != current_app.config["ADMIN_KEY"]:
            return {"message": "Incorrect admin key."}, 403

        register(data["username"], data["email"], data["password"], has_key)
        return {"message": "Succesfully created user."}, 201
