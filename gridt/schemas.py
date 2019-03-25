from marshmallow import Schema, fields, validates_schema, ValidationError
from marshmallow.validate import Length


class NewUserSchema(Schema):
    username = fields.Str(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class IntervalSchema(Schema):
    days = fields.Int(required=True)
    hours = fields.Int(required=True)

    @validates_schema
    def check_nonzero(self, in_data):
        if in_data["days"] <= 0 and in_data["hours"] <= 0:
            raise ValidationError("Interval must be nonzero.")


class MovementSchema(Schema):
    name = fields.Str(required=True, validate=Length(min=4, max=50))
    short_description = fields.Str(required=True, validate=Length(min=10, max=100))
    description = fields.Str()
    interval = fields.Nested(IntervalSchema(), required=True)
