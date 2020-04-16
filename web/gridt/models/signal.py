from datetime import datetime
from sqlalchemy import asc, desc
from gridt.db import db


class Signal(db.Model):
    """
    Representation of signals in the database.

    :attribute leader: The leader that created this signal.
    :attribute movement: The movement that this signal was created in.
    :attribute message: Message from the leader.
    """

    __tablename__ = "signals"
    id = db.Column(db.Integer, primary_key=True)
    leader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movements.id"))
    time_stamp = db.Column(db.DateTime(timezone=True), nullable=False)
    message = db.Column(db.String(140))

    leader = db.relationship("User")
    movement = db.relationship("Movement")

    def __init__(self, leader, movement, message=None):
        self.leader = leader
        self.movement = movement
        self.time_stamp = self._get_now()
        self.message = message

    @classmethod
    def find_last(cls, user, movement, n=1):
        return (
            cls.query.filter_by(leader=user, movement=movement)
            .order_by(desc("time_stamp"))
            .first()
        )

    @classmethod
    def get_signal_history(cls, user, movement, n):
        return (
            cls.query.filter_by(leader=user, movement=movement)
            .order_by(desc("time_stamp"))
            .limit(n)
            .all()
        )

    def _get_now(self):
        """
        Useful for patching in tests.
        """
        return datetime.now()

    def dictify(self):
        signal_dict = {
            "time_stamp": str(self.time_stamp.astimezone()),
        }

        if self.message:
            signal_dict["message"] = self.message

        return signal_dict

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
