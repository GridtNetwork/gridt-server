from db import db

association_movement_users = db.Table(
    'movement_user', db.Model.metadata,
    db.Column('movement_id', db.Integer, db.ForeignKey('movements.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'))
)


