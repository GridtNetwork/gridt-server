from flask import request
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from marshmallow import ValidationError

from gridt_server.schemas import MovementSchema
from gridt_server.models.movement import Movement
from gridt_server.models.user import User
from gridt_server.models.signal import Signal

from .helpers import get_movement, schema_loader

from gridt.controllers.follower import get_subscriptions
from gridt.controllers.movements import get_all_movements


class MovementsResource(Resource):
    schema = MovementSchema()

    @jwt_required
    def get(self):
        return get_all_movements(get_jwt_identity())

    @jwt_required
    def post(self):
        current_identity = User.query.get(get_jwt_identity())
        data = schema_loader(self.schema, request.get_json())

        movement = Movement(
            data["name"],
            data["interval"],
            short_description=data["short_description"],
            description=data.get("description"),
        )
        movement.save_to_db()
        movement.add_user(current_identity)

        return {"message": "Successfully created movement."}, 201


class SubscriptionsResource(Resource):
    @jwt_required
    def get(self):
        return get_subscriptions(get_jwt_identity())


class SingleMovementResource(Resource):
    @jwt_required
    def get(self, identifier):
        current_identity = User.query.get(get_jwt_identity())

        movement = get_movement(identifier)
        return movement.dictify(current_identity), 200


class SubscribeResource(Resource):
    @jwt_required
    def put(self, movement_id):
        current_identity = User.query.get(get_jwt_identity())

        movement = get_movement(movement_id)
        if not current_identity in movement.current_users:
            movement.add_user(current_identity)
        return {"message": "Successfully subscribed to this movement."}, 200

    @jwt_required
    def delete(self, movement_id):
        current_identity = User.query.get(get_jwt_identity())

        movement = get_movement(movement_id)
        if current_identity in movement.current_users:
            movement.remove_user(current_identity)
        return {"message": "Successfully unsubscribed from this movement."}, 200


class NewSignalResource(Resource):
    @jwt_required
    def post(self, movement_id):
        current_identity = User.query.get(get_jwt_identity())

        movement = get_movement(movement_id)
        if current_identity not in movement.current_users:
            return {"message": "User is not subscribed to this movement."}, 400

        message = None
        if request.get_json():
            message = request.get_json().get("message")

        signal = Signal(current_identity, movement, message)
        signal.save_to_db()

        return {"message": "Successfully created signal."}, 201
