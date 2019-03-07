import random
from sqlalchemy import not_, and_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import joinedload

from db import db

from models.user import User
from models.movement_user_association import MovementUserAssociation


class Movement(db.Model):
    __tablename__ = "movements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    short_description = db.Column(db.String(100))
    description = db.Column(db.String(1000))

    user_associations = db.relationship(
        "MovementUserAssociation", back_populates="movement"
    )
    users = association_proxy("user_associations", "follower")

    def __init__(self, name, short_description=None):
        self.name = name
        self.short_description = short_description

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    def add_user(self, user):
        for i in range(4):

            def get_association_leader(association):
                if association.leader:
                    return association.leader.id

            associations_in_movement = list(
                filter(lambda a: a.movement == self, user.follower_associations)
            )

            current_leader_ids = list(
                map(get_association_leader, associations_in_movement)
            )

            possible_leaders = (
                db.session.query(User)
                .filter(
                    and_(
                        not_(User.id == user.id),
                        not_(User.id.in_(current_leader_ids)),
                        User.movements.any(id=self.id),
                    )
                )
                .all()
            )

            assoc = MovementUserAssociation(self, user)
            if possible_leaders:
                assoc.leader = random.choice(possible_leaders)

            assoc.save_to_db()
