from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from gridt_server.schemas import (
    MovementSchema,
    SingleMovementSchema,
    SignalSchema,
)

from .helpers import schema_loader

from src.controllers.subscription import (
    get_subscriptions,
    new_subscription,
    is_subscribed
)
from src.controllers.movements import (
    get_all_movements,
    get_movement
)

from src.controllers.creation import (
    remove_creation,
    new_movement_by_user,
)
from src.controllers.leader import send_signal


class MovementsResource(Resource):
    schema = MovementSchema()

    @jwt_required
    def get(self):
        return get_all_movements(get_jwt_identity())

    @jwt_required
    def post(self):
        data = schema_loader(self.schema, request.get_json())
        new_movement_by_user(
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
        new_subscription(get_jwt_identity(), movement_id)
        return {"message": "Successfully subscribed to this movement."}

    @jwt_required
    def delete(self, movement_id):
        schema_loader(self.schema, {"movement_id": movement_id})
        # HTTP DELETE request is idempotent, meaning that it should not matter
        # if the user is subscribed or not, if he is, he should be removed.
        if is_subscribed(get_jwt_identity(), movement_id):
            remove_creation(get_jwt_identity(), movement_id)
        return {"message": "Successfully unsubscribed from this movement."}


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
