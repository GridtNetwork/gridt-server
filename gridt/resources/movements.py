from datetime import timedelta

from flask import current_app, request
from flask_restful import Resource
from flask_jwt import jwt_required, current_identity

from gridt.schemas import MovementSchema
from gridt.models.movement import Movement


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
            timedelta(days=res.data["interval"]["days"], hours=res.data["interval"]["hours"]),
            short_description=res.data["short_description"],
        )
        movement.save_to_db()
        return {"message": "Successfully created movement."}, 201
