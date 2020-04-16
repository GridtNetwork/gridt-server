from flask import request
from flask_restful import Resource, abort
from flask_jwt import jwt_required, current_identity

from marshmallow import ValidationError

from gridt.schemas import MovementSchema
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.signal import Signal

from .helpers import get_user, get_movement


class MovementsResource(Resource):
    schema = MovementSchema()

    @jwt_required()
    def get(self):
        movements = Movement.query.all()
        movement_dicts = [movement.dictify(current_identity) for movement in movements]
        return movement_dicts, 200

    @jwt_required()
    def post(self):
        try:
            res = self.schema.load(request.get_json())
        except ValidationError as error:
            field = list(error.messages.keys())[0]
            return {"message": f"{field}: {error.messages[field][0]}"}, 400

        existing_movement = Movement.find_by_name(res["name"])
        if existing_movement:
            return (
                {
                    "message": "Could not create movement, because movement name is already in use."
                },
                400,
            )

        movement = Movement(
            res["name"],
            res["interval"],
            short_description=res["short_description"],
            description=res.get("description"),
        )
        movement.save_to_db()

        return {"message": "Successfully created movement."}, 201


class SubscriptionsResource(Resource):
    @jwt_required()
    def get(self):
        movements = set(current_identity.movements)
        movement_dicts = [movement.dictify(current_identity) for movement in movements]
        return movement_dicts, 200


class SingleMovementResource(Resource):
    @jwt_required()
    def get(self, identifier):
        movement = get_movement(identifier)
        return movement.dictify(current_identity), 200


class SubscribeResource(Resource):
    @jwt_required()
    def put(self, movement_id):
        movement = get_movement(movement_id)
        if not current_identity in movement.users:
            movement.add_user(current_identity)
        return {"message": "Successfully subscribed to this movement."}, 200

    @jwt_required()
    def delete(self, movement_id):
        movement = get_movement(movement_id)
        if current_identity in movement.users:
            movement.remove_user(current_identity)
        return {"message": "Successfully unsubscribed from this movement."}, 200


class NewSignalResource(Resource):
    @jwt_required()
    def post(self, movement_id):
        movement = get_movement(movement_id)
        if current_identity not in movement.users:
            return {"message": "User is not subscribed to this movement."}, 400

        message = None
        if request.get_json():
            message = request.get_json().get("message")

        signal = Signal(current_identity, movement, message)
        signal.save_to_db()

        return {"message": "Successfully created signal."}, 201
