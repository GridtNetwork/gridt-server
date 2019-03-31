from flask import request
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from gridt.models.user import User
from gridt.schemas import NewUserSchema


class LoggedInResource(Resource):
    @jwt_required()
    def get(self):
        return {"message": f"Hi { current_identity.username }, you are logged in."}, 200


class RegisterResource(Resource):
    def post(self):
        schema = NewUserSchema()
        result = schema.load(request.get_json())
        if result.errors:
            return {"message": "Bad request"}, 400
        data = result.data

        if User.find_by_name(data["username"]):
            return {"message": "Username already in use."}, 400

        user = User(data["username"], data["email"], data["password"])
        user.save_to_db()

        return {"message": "Succesfully created user."}, 201
