import random
from sqlalchemy import not_, and_
from sqlalchemy.types import Interval
from sqlalchemy.ext.associationproxy import association_proxy

from gridt.db import db

from gridt.models.user import User
from gridt.models.movement_user_association import MovementUserAssociation


class Movement(db.Model):
    """
    Intuitive representation of movements in the database. ::

        from datetime import timedelta
        flossing = Movement('flossing', timedelta(days=2))
        robin = User.find_by_id(1)
        pieter = User.find_by_id(2)
        jorn = User.find_by_id(3)
        flossing.users = [robin, pieter, jorn]
        flossing.save_to_db()

    :Note: changes are only saved to the database when :func:`Movement.save_to_db` is called.

    :param name: Name of the movement
    :param short_description: Give a short description for your movement.
    :attribute description: More elaborate description of your movement.
    :attribute users: All user that have been subscribed to this movement.
    :attribute user_associations: All instances of :class:`models.movement_user_association.MovementUserAssociation` with that link to this movement.
    """

    __tablename__ = "movements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    interval = db.Column(db.Interval, nullable=False)
    short_description = db.Column(db.String(100))
    description = db.Column(db.String(1000))

    user_associations = db.relationship(
        "MovementUserAssociation",
        back_populates="movement",
        cascade="all, delete-orphan",
    )

    users = association_proxy(
        "user_associations",
        "follower",
        creator=lambda user: MovementUserAssociation(follower=user),
    )

    def __init__(self, name, interval, short_description=None):
        self.name = name
        self.interval = interval
        self.short_description = short_description

    def save_to_db(self):
        """
        Store this movement in the database, making changes to the movement permanent.
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        Delete this movement from the database.

        :warning: This is permanent and irrevocable.
        """
        db.session.delete(self)
        db.session.commit()

    def add_user(self, user):
        """
        Add a new user to self.users and give it appropriate leaders.

        :param user: the user that is to be subscribed to this movement

        :todo: Move find leader logic into private function.
        """
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

    def remove_user(self, user):
        """
        Remove any relationship this user previously had with this movement.
        Deleting any leader as well as follower relationship.

        :param user: user to be deleted.
        """
        # This must be done so that no empty user associations with just a
        # movement and a leader are left.
        for asso in self.user_associations:
            if asso.follower == user:
                asso.delete_from_db()
        self.users = list(filter(lambda u: u != user, self.users))
