import random
from sqlalchemy import not_, and_
from sqlalchemy.types import Interval
from sqlalchemy.ext.associationproxy import association_proxy

from gridt.db import db

from gridt.models.user import User
from gridt.models.update import Update
from gridt.models.movement_user_association import MovementUserAssociation


class Movement(db.Model):
    """
    Intuitive representation of movements in the database. ::

        from datetime import timedelta
        flossing = Movement('flossing', timedelta(days=2))
        robin = User.find_by_id(1)
        pieter = User.find_by_id(2)
        jorn = User.find_by_id(3) flossing.users = [robin, pieter, jorn]
        flossing.save_to_db()

    :Note: changes are only saved to the database when :func:`Movement.save_to_db` is called.

    :param str name: Name of the movement
    :param datetime.timedelta interval: Interval in which the user is supposed to repeat the action.
    :param str short_description: Give a short description for your movement.
    :attribute str description: More elaborate description of your movement.
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

    def __init__(self, name, interval, short_description=""):
        self.name = name
        self.interval = interval
        self.short_description = short_description
        self.description = ""

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
    def find_by_id(cls, id_):
        """
        Find a movement by it's id.
        :param id_: Id of movement that is being queried.
        :rtype: None or gridt.models.movement.Movement
        """
        return cls.query.get(id_)

    def _find_possible_leaders_ids(self, user, exclude=None):
        """
        Private function to look for ids of leaders that this user could use.

        :param gridt.models.user.User user: User that needs new leaders.
        :param list exclude: List of users (can be a user model or an id) to exclude from search.
        :returns: A list of ids of users, or None if the user is not in this movement.
        """

        if user.leaders(self) is None:
            return None

        current_leader_ids = [leader.id for leader in user.leaders(self)]

        possible_leaders = [
            tup[0]
            for tup in db.session.query(User.id)
            .filter(
                and_(
                    not_(User.id == user.id),
                    not_(User.id.in_(current_leader_ids)),
                    User.movements.any(id=self.id),
                )
            )
            .all()
        ]

        if exclude:

            if type(exclude[0]) == int:
                exclude_ids = exclude
            if type(exclude[0]) == type(user):
                exclude_ids = [user.id for user in exclude]

            possible_leaders = list(
                filter(lambda l: l not in exclude_ids, possible_leaders)
            )

        return possible_leaders

    def swap_leader(self, user, leader):
        """
        Swap out the presented leader in the users leaders.

        :param user: User who's leader will be swapped.
        :param leader: The leader that will be swapped.
        :return: True if successful, False if unsuccesful.
        :rtype bool:
        """
        # We can not change someone's leader if they are not already following that leader.
        if leader and leader not in user.leaders(self):
            return False

        # If there is no other possible leaders than we can't perform the swap.
        possible_leaders = self._find_possible_leaders_ids(user, user.leaders(self))
        if not possible_leaders:
            return False

        new_leader = User.find_by_id(random.choice(possible_leaders))
        for association in user.follower_associations:
            if association.leader == leader:
                association.leader = new_leader

        return True

    def add_user(self, user):
        """
        Add a new user to self.users and give it appropriate leaders.

        :param gridt.models.user.User user: the user that is to be subscribed to this movement

        :todo: Move find leader logic into private function.
        """
        for i in range(4):
            possible_leaders = self._find_possible_leaders_ids(user)

            assoc = MovementUserAssociation(self, user)
            if possible_leaders:
                assoc.leader = User.find_by_id(random.choice(possible_leaders))

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
            "interval": {
                "days": self.interval.days,
                "hours": self.interval.seconds // 3600,
            },
        }

        movement_dict["subscribed"] = False
        if user in self.users:
            movement_dict["subscribed"] = True
            movement_dict["leaders"] = [
                {
                    "username": user.username,
                    "id": user.id,
                    "last-update": str(Update.find_last(user, self).time_stamp)
                    if Update.find_last(user, self)
                    else None,
                }
                for user in user.leaders(self)
            ]

        return movement_dict
