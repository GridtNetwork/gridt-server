from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from gridt_server.schemas import (
    MovementSchema,
    SingleMovementSchema,
    SignalSchema,
)

from .helpers import schema_loader

from gridt.controllers.subscription import (
    get_subscriptions,
    new_subscription,
    remove_subscription,
    is_subscribed
)
from gridt.controllers.movements import (
    get_all_movements,
    get_movement
)
import gridt.exc as GridtExpections
from gridt.controllers.creation import (
    new_movement_by_user,
)
from gridt.controllers.leader import send_signal


class MovementsResource(Resource):
    schema = MovementSchema()

    @jwt_required()
    def get(self):
        return get_all_movements(get_jwt_identity())

    @jwt_required()
    def post(self):
        data = schema_loader(self.schema, request.get_json())
        try:
            new_movement_by_user(
                user_id=get_jwt_identity(),
                name=data["name"],
                interval=data["interval"],
                short_description=data.get("short_description"),
                description=data.get("long_description"),
            )
        except GridtExpections.UserNotAdmin:
            message = "Insufficient privileges to create a movement."
            return {"message": message}, 403
        return {"message": "Successfully created movement."}, 201


class SubscriptionsResource(Resource):
    @jwt_required()
    def get(self):
        return get_subscriptions(get_jwt_identity())


class SingleMovementResource(Resource):
    schema = SingleMovementSchema()

    @jwt_required()
    def get(self, identifier):
        schema_loader(self.schema, {"movement_id": identifier})
        return get_movement(int(identifier), get_jwt_identity())


class SubscribeResource(Resource):
    schema = SingleMovementSchema()

    @jwt_required()
    def put(self, movement_id):
        schema_loader(self.schema, {"movement_id": movement_id})
        user_id = get_jwt_identity()
        if not is_subscribed(user_id, int(movement_id)):
            new_subscription(user_id, int(movement_id))
        return {"message": "Successfully subscribed to this movement."}

    @jwt_required()
    def delete(self, movement_id):
        schema_loader(self.schema, {"movement_id": movement_id})
        # HTTP DELETE request is idempotent, meaning that it should not matter
        # if the user is subscribed or not, if he is, he should be removed.
        if is_subscribed(get_jwt_identity(), int(movement_id)):
            remove_subscription(get_jwt_identity(), int(movement_id))
        return {"message": "Successfully unsubscribed from this movement."}


class NewSignalResource(Resource):
    schema = SignalSchema()

    @jwt_required()
    def post(self, movement_id):
        schema_loader(
            self.schema, {"leader_id": get_jwt_identity(), "movement_id": movement_id},
        )
        message = None
        if request.get_json(silent=True):
            message = request.get_json().get("message")

        send_signal(get_jwt_identity(), int(movement_id), message)

        return {"message": "Successfully created signal."}, 201
