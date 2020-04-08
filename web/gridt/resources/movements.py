from flask import request
from flask_restful import Resource, abort
from flask_jwt import jwt_required, current_identity

from marshmallow import ValidationError

from gridt.schemas import MovementSchema
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.signal import Signal


def get_movement(identifier):
    try:
        identifier = int(identifier)
        movement = Movement.find_by_id(identifier)
    except ValueError:
        movement = Movement.find_by_name(identifier)

    if not movement:
        abort(404, message="This movement does not exist.")

    return movement


def get_user(identifier):
    try:
        identifier = int(identifier)
        user = User.find_by_id(identifier)
    except ValueError:
        user = User.find_by_name(identifier)

    return user


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


class SwapLeaderResource(Resource):
    @jwt_required()
    def post(self, movement_id, leader_id):
        movement = get_movement(movement_id)

        if not current_identity in movement.users:
            return {"message": "User is not subscribed to this movement."}, 400

        leader = get_user(leader_id)

        # This prevents a malicious user from finding user ids.
        # Returning a 404 for a nonexistant user would give them more
        # infromation than we want to share.
        if not leader or leader not in current_identity.leaders(movement):
            return {"message": "User is not following this leader."}, 400

        new_leader = movement.swap_leader(current_identity, leader)

        if not new_leader:
            return {"message": "Could not find leader to replace the current one."}

        time_stamp = None
        if Signal.find_last(new_leader, movement):
            time_stamp = str(Signal.find_last(new_leader, movement).time_stamp)

        return (
            {
                "id": new_leader.id,
                "username": new_leader.username,
                "last_signal": time_stamp,
            },
            200,
        )


class NewSignalResource(Resource):
    @jwt_required()
    def post(self, movement_id):
        movement = get_movement(movement_id)
        if current_identity not in movement.users:
            return {"message": "User is not subscribed to this movement."}, 400

        signal = Signal(current_identity, movement)
        signal.save_to_db()

        return {"message": "Successfully created signal."}, 201
