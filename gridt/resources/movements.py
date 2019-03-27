from datetime import timedelta
from random import choice

from flask import current_app, request
from flask_restful import Resource, abort
from flask_jwt import jwt_required, current_identity

from gridt.schemas import MovementSchema
from gridt.models.movement import Movement
from gridt.models.user import User
from gridt.models.update import Update


def get_movement(identifier):
    movement = None
    try:
        identifier = int(identifier)
        movement = Movement.find_by_id(identifier)
    except ValueError:
        movement = Movement.find_by_name(identifier)

    if not movement:
        # return {"message": "This movement does not exist."}, 404
        abort(404, message="This movement does not exist.")
    return movement


def get_user(identifier):
    user = None
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
        res = self.schema.load(request.get_json())
        if res.errors:
            if res.errors.get("interval"):
                return {"message": res.errors["interval"]["_schema"][0]}, 400
            field = list(res.errors.keys())[0]
            return {"message": f"{field}: {res.errors[field][0]}"}, 400
        existing_movement = Movement.find_by_name(res.data["name"])
        if existing_movement:
            return (
                {"message": "Could not create movement, because it already exists."},
                400,
            )

        movement = Movement(
            res.data["name"],
            timedelta(
                days=res.data["interval"]["days"], hours=res.data["interval"]["hours"]
            ),
            short_description=res.data["short_description"],
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
    def delete(self, identifier):
        movement = get_movement(identifier)
        if current_identity in movement.users:
            movement.remove_user(current_identity)
        return {"message": "Successfully unsubscribed from this movement."}, 200


class FindLeaderResource(Resource):
    @jwt_required()
    def post(self, movement_id):
        movement = get_movement(movement_id)
        if not current_identity in movement.users:
            return {"message": "User is not subscribed to this movement."}, 400

        if len(current_identity.leaders(movement)) == 4:
            return {"message": "This user has no more space for more leaders."}, 400

        if not movement._find_possible_leaders_ids(current_identity):
            return {"message": "No leader found."}, 500

        possible_leaders_ids = movement._find_possible_leaders_ids(current_identity)
        leader = User.find_by_id(random.choice(possible_leaders_ids))
        movement.add_leader(current_identity, leader)

        last_update = str(Update.find_last(leader, movement).time_stamp)

        return {
            "id": leader.id,
            "username": leader.username,
            "last_update": last_update,
        }


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
        if not leader or not leader in movement.users:
            return {"message": "User is not following this leader."}, 400

        new_leader = movement.swap_leader(current_identity, leader)

        time_stamp = None
        if Update.find_last(new_leader, movement):
            time_stamp = str(Update.find_last(new_leader, movement).time_stamp)

        return (
            {
                "id": new_leader.id,
                "username": new_leader.username,
                "last_update": time_stamp,
            },
            200,
        )


class NewUpdateResource(Resource):
    @jwt_required()
    def post(self, movement_id):
        movement = get_movement(movement_id)
        if current_identity not in movement.users:
            return {"message": "User is not subscribed to this movement."}, 400

        update = Update(current_identity, movement)
        update.save_to_db()

        return {"message": "Successfully created update."}, 200
