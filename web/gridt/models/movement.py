import random
from sqlalchemy import not_, and_
from sqlalchemy.ext.associationproxy import association_proxy

from gridt.db import db

from gridt.models.user import User
from gridt.models.update import Signal
from gridt.models.movement_user_association import MovementUserAssociation


class Movement(db.Model):
    """
    Intuitive representation of movements in the database. ::

        flossing = Movement('flossing', 'daily')
        robin = User.find_by_id(1)
        pieter = User.find_by_id(2)
        jorn = User.find_by_id(3) flossing.users = [robin, pieter, jorn]
        flossing.save_to_db()

    :Note: changes are only saved to the database when :func:`Movement.save_to_db` is called.

    :param str name: Name of the movement
    :param str interval: Interval in which the user is supposed to repeat the action.
    :param str short_description: Give a short description for your movement.
    :attribute str description: More elaborate description of your movement.
    :attribute users: All user that have been subscribed to this movement.
    :attribute user_associations: All instances of :class:`models.movement_user_association.MovementUserAssociation` with that link to this movement.
    """

    __tablename__ = "movements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    interval = db.Column(db.String(20), nullable=False)
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

    def __init__(self, name, interval, short_description="", description=""):
        self.name = name
        self.interval = interval
        self.short_description = short_description
        self.description = description

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

    @classmethod
    def find_by_name(cls, name):
        """
        Find a movement by it's name.
        :param name: Name of movement that is being queried.
        :rtype: None or gridt.models.movement.Movement
        """
        return cls.query.filter_by(name=name).one_or_none()

    @classmethod
    def find_by_id(cls, identifier):
        """
        Find a movement by it's id.
        :param identifier: Id of movement that is being queried.
        :rtype: None or gridt.models.movement.Movement
        """
        return cls.query.get(identifier)

    def find_leaders(self, user, exclude=[]):
        """
        Private function to look for ids of leaders that this user could use.

        :param gridt.models.user.User user: User that needs new leaders.
        :param list exclude: List of users (can be a user model or an id) to exclude from search.
        :returns: A list of ids of users, or None if the user is not in this movement.
        """
        current_leader_ids = [leader.id for leader in user.leaders(self)]
        if exclude:
            if type(exclude[0]) == type(user):
                exclude = [u.id for u in exclude]

        return (
            User.query.join(User.follower_associations)
            .filter(
                not_(User.id == user.id),
                not_(User.id.in_(current_leader_ids)),
                not_(User.id.in_(exclude)),
                MovementUserAssociation.movement_id == self.id,
            )
            .group_by(User.id)
            .all()
        )

    def swap_leader(self, user, leader):
        """
        Swap out the presented leader in the users leaders.

        :param user: User who's leader will be swapped.
        :param leader: The leader that will be swapped.
        :return: New leader or None
        """
        # We can not change someone's leader if they are not already following that leader.
        if leader and leader not in user.leaders(self):
            raise ValueError("User is not following that leader.")

        # If there is no other possible leaders than we can't perform the swap.
        possible_leaders = self.find_leaders(user)
        if not possible_leaders:
            return None

        new_leader = random.choice(possible_leaders)
        for association in user.follower_associations:
            if association.leader == leader and association.movement == self:
                association.leader = new_leader
                association.save_to_db()

        return new_leader

    def add_user(self, user):
        """
        Add a new user to self.users and give it appropriate leaders. Find followers without leaders and the user as a leader.

        :param gridt.models.user.User user: the user that is to be subscribed to this movement

        :todo: Move find leader logic into private function.
        """
        for i in range(4):
            possible_leaders = self.find_leaders(user)

            assoc = MovementUserAssociation(self, user)
            if possible_leaders:
                assoc.leader = random.choice(possible_leaders)

            assoc.save_to_db()

        leaderless = (
            db.session.query(MovementUserAssociation)
            .filter(
                not_(MovementUserAssociation.follower_id == user.id),
                MovementUserAssociation.leader_id == None,
                MovementUserAssociation.movement_id == self.id,
            )
            .group_by(MovementUserAssociation.follower_id)
            .all()
        )

        for association in leaderless:
            association.leader = user
            association.save_to_db()

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

    def dictify(self, user):
        """
        Return a dict version of this movement, ready for shipping to JSON.

        :param user: The user that requests the information.
        """
        movement_dict = {
            "name": self.name,
            "id": self.id,
            "short_description": self.short_description,
            "description": self.description,
            "interval": self.interval,
        }

        movement_dict["subscribed"] = False
        if user in self.users:
            movement_dict["subscribed"] = True
            last_signal = Signal.find_last(user, self)
            movement_dict["last_signal_sent"] = (
                {"time_stamp": str(last_signal.time_stamp.astimezone())}
                if last_signal
                else None
            )
            movement_dict["leaders"] = [
                {
                    "username": leader.username,
                    "id": leader.id,
                    "last_signal": str(
                        Signal.find_last(leader, self).time_stamp.astimezone()
                    )
                    if Signal.find_last(leader, self)
                    else None,
                }
                for leader in user.leaders(self)
            ]

        return movement_dict
