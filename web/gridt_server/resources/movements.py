from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from gridt_server.schemas import (
    MovementSchema,
    SingleMovementSchema,
    SignalSchema,
)
from gridt_server.models.user import User

from .helpers import schema_loader

from gridt.controllers.follower import get_subscriptions
from gridt.controllers.movements import (
    get_all_movements,
    get_movement,
    subscribe,
)
from gridt.controllers.leader import send_signal
from gridt.controllers.movements import new_movement


class MovementsResource(Resource):
    schema = MovementSchema()

    @jwt_required
    def get(self):
        return get_all_movements(get_jwt_identity())

    @jwt_required
    def post(self):
        data = schema_loader(self.schema, request.get_json())
        new_movement(
            get_jwt_identity(),
            data["name"],
            data["interval"],
            data["short_description"],
            data.get("long_description"),
        )
        return {"message": "Successfully created movement."}, 201


class SubscriptionsResource(Resource):
    @jwt_required
    def get(self):
        return get_subscriptions(get_jwt_identity())


class SingleMovementResource(Resource):
    schema = SingleMovementSchema()

    @jwt_required
    def get(self, identifier):
        schema_loader(self.schema, {"movement_id": identifier})
        return get_movement(identifier, get_jwt_identity())


class SubscribeResource(Resource):
    schema = SingleMovementSchema()

    @jwt_required
    def put(self, movement_id):
        schema_loader(self.schema, {"movement_id": movement_id})
        subscribe(get_jwt_identity(), movement_id)
        return {"message": "Successfully subscribed to this movement."}, 200

    @jwt_required
    def delete(self, movement_id):
        current_identity = User.query.get(get_jwt_identity())

        movement = get_movement(movement_id)
        if current_identity in movement.current_users:
            movement.remove_user(current_identity)
        return {"message": "Successfully unsubscribed from this movement."}, 200


class NewSignalResource(Resource):
    schema = SignalSchema()

    @jwt_required
    def post(self, movement_id):
        schema_loader(
            self.schema, {"leader_id": get_jwt_identity(), "movement_id": movement_id},
        )
        message = None
        if request.get_json():
            message = request.get_json().get("message")

        send_signal(get_jwt_identity(), movement_id, message)

        return {"message": "Successfully created signal."}, 201
