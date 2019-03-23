from flask import current_app
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from gridt.models.movement import Movement


class MovementsResource(Resource):
    @jwt_required()
    def get(self):
        movements = Movement.query.all()
        movement_dicts = [movement.dictify(current_identity) for movement in movements]
        return movement_dicts, 200

    @jwt_required()
    def post(self):
        pass
