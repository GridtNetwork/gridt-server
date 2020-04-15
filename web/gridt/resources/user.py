from flask import request
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from marshmallow import ValidationError

from gridt.models.user import User
from gridt.schemas import BioSchema


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
