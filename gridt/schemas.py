from marshmallow import Schema, fields


class NewUserSchema(Schema):
    username = fields.Str(required=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)


class IntervalSchema(Schema):
    days = fields.Int()
    hours = fields.Int()


class MovementSchema(Schema):
    name = fields.Str(required=True)
    short_description = fields.Str(required=True)
    description = fields.Str()
    interval = fields.Nested(IntervalSchema())
