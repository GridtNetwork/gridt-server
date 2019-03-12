from flask import request
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity
from marshmallow import ValidationError

from models.user import User
from schemas import NewUserSchema

class LoggedInResource(Resource):
    @jwt_required()
    def get(self):
        return {"message": f"Hi { current_identity.username }, you are logged in."}, 200

class RegisterResource(Resource):
    def post(self):
        schema = NewUserSchema()
        try:
            data = schema.load(request.get_json(), partial=True).data
        except ValidationError:
            return {'message': 'Bad request'}, 400

        if User.find_by_name(data['username']):
            return {'message': 'Username already in use'}, 400

        user = User(data['username'], data['password'])
        user.save_to_db()

        return {'message': 'Succesfully created user'}, 200
