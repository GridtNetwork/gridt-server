import random
from datetime import datetime
from sqlalchemy import not_, and_
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import func

from gridt_server.db import db

from gridt_server.models.user import User
from gridt_server.models.signal import Signal
from gridt_server.models.movement_user_association import MovementUserAssociation


class Movement(db.Model):
    """
    Intuitive representation of movements in the database. ::

        flossing = Movement('flossing', 'daily')
        robin = User.find_by_id(1)
        pieter = User.find_by_id(2)
        jorn = User.find_by_id(3)
        flossing.users = [robin, pieter, jorn]
        flossing.save_to_db()

    :Note: changes are only saved to the database when :func:`Movement.save_to_db`
    is called.

    :param str name: Name of the movement
    :param str interval: Interval in which the user is supposed to repeat the action.
    :param str short_description: Give a short description for your movement.
    :attribute str description: More elaborate description of your movement.
    :attribute users: All user that have been subscribed to this movement.
    :attribute user_associations: All instances of
    :class:`models.movement_user_association.MovementUserAssociation` with that
    link to this movement.
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

    @property
    def current_users(self):
        return (
            User.query.join(User.follower_associations)
            .filter(
                MovementUserAssociation.movement_id == self.id,
                MovementUserAssociation.destroyed == None,
            )
            .group_by(User.id)
            .all()
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
        :param list exclude: List of users (can be a user model or an id) to
        exclude from search.
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
        if not leader:
            raise ValueError("Cannot swap a leader that does not exist.")

        # We can not change someone's leader if they are not already
        # following that leader.
        if leader and leader not in user.leaders(self):
            raise ValueError("User is not following that leader.")

        # If there are no other possible leaders than we can't perform the swap.
        possible_leaders = self.find_leaders(user)
        if not possible_leaders:
            return None

        mua = MovementUserAssociation.query.filter(
            MovementUserAssociation.follower_id == user.id,
            MovementUserAssociation.leader_id == leader.id,
            MovementUserAssociation.movement_id == self.id,
            MovementUserAssociation.destroyed == None,
        ).one()

        mua.destroy()

        new_leader = random.choice(possible_leaders)
        new_assoc = MovementUserAssociation(self, user, new_leader)

        new_assoc.save_to_db()

        return new_leader

    def find_leaderless(self, user):
        """
        Find the active users in this movement
        (movement.current_users) that have fewer than four leaders.
        These users should not be user and not have user as leader.
        """
        MUA = MovementUserAssociation

        leader_associations = [
            r[0]
            for r in db.session.query(MUA.follower_id)
            .filter(MUA.movement_id == self.id, MUA.leader_id == user.id)
            .all()
        ]

        valid_muas = (
            db.session.query(MUA, func.count().label("mua_count"),)
            .filter(MUA.movement_id == self.id, MUA.destroyed == None,)
            .group_by(MUA.follower_id)
            .subquery()
        )

        leaderless = (
            db.session.query(User)
            .join(User.follower_associations)
            .filter(
                not_(User.id == user.id),
                valid_muas.c.follower_id == User.id,
                valid_muas.c.mua_count < 4,
            )
            .group_by(MUA.follower_id)
            .filter(not_(User.id.in_(leader_associations)))
        )

        return leaderless

    def add_user(self, user):
        """
        Add a new user to self.users and give it appropriate leaders.

        :param gridt.models.user.User user: the user that is to be
        subscribed to this movement
        """
        while len(user.leaders(self)) < 4:
            possible_leaders = self.find_leaders(user)
            if possible_leaders:
                assoc = MovementUserAssociation(self, user)
                assoc.leader = random.choice(possible_leaders)
                assoc.save_to_db()
            else:
                if len(user.leaders(self)) == 0:
                    assoc = MovementUserAssociation(self, user, None)
                    assoc.save_to_db()
                    break
                else:
                    break

        # Bug: the following will allow "excluded" leaders to rejoin
        # the movement and "force" excluding users with too few leaders
        # into MUA. Can we give users an attribute "exclude" instead?
        # It will span all of Gridt, not just a single movement.
        leaderless = self.find_leaderless(user)
        for new_follower in leaderless:
            association = MovementUserAssociation(self, new_follower, user)
            association.save_to_db()

            assoc_none = (
                db.session.query(MovementUserAssociation)
                .filter(
                    MovementUserAssociation.movement_id == self.id,
                    MovementUserAssociation.follower_id == new_follower.id,
                    MovementUserAssociation.leader_id == None,
                )
                .group_by(MovementUserAssociation.follower_id)
                .all()
            )
            for a in assoc_none:
                a.destroy()

    def remove_user(self, user):
        """
        Remove any relationship this user previously had with this movement.
        Deleting any leader as well as follower relationship.

        :param user: user to be deleted.
        """
        leader_muas_to_destroy = (
            db.session.query(MovementUserAssociation)
            .filter(
                MovementUserAssociation.movement_id == self.id,
                MovementUserAssociation.destroyed == None,
                MovementUserAssociation.leader_id == user.id,
            )
            .all()
        )

        follower_muas_to_destroy = (
            db.session.query(MovementUserAssociation)
            .filter(
                MovementUserAssociation.movement_id == self.id,
                MovementUserAssociation.destroyed == None,
                MovementUserAssociation.follower_id == user.id,
            )
            .all()
        )

        for mua in follower_muas_to_destroy:
            mua.destroy()
            mua.save_to_db()

        for mua in leader_muas_to_destroy:
            possible_leaders = self.find_leaders(mua.follower)
            mua.destroy()
            mua.save_to_db()
            # Add new MUAs for each former follower.
            if possible_leaders:
                new_leader = random.choice(possible_leaders)
                new_mua = MovementUserAssociation(self, mua.follower, new_leader)
            else:
                new_mua = MovementUserAssociation(self, mua.follower, None)
            new_mua.save_to_db()

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
        if user in self.current_users:
            movement_dict["subscribed"] = True

            last_signal = Signal.find_last(user, self)
            movement_dict["last_signal_sent"] = (
                {"time_stamp": str(last_signal.time_stamp.astimezone())}
                if last_signal
                else None
            )

            # Extend the user dictionary with the last signal
            movement_dict["leaders"] = [
                dict(
                    leader.dictify(),
                    **(
                        {"last_signal": Signal.find_last(leader, self).dictify()}
                        if Signal.find_last(leader, self)
                        else {}
                    )
                )
                for leader in user.leaders(self)
            ]

        return movement_dict
