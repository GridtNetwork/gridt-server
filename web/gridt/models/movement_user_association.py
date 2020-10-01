from datetime import datetime

from gridt.db import db


class MovementUserAssociation(db.Model):
    """
    Association class that lies at the foundation of the network.
    Think of this class as the arrows that connect followers with leaders Association class that lies at the foundation of the network.
    Think of this class as the arrows that connect followers with leaders
    within their respective circle of the movement.
    within their respective circle of the movement.

    :param model.user.User follower: User that will be following.
    :param model.user.User leader: User that will lead.
    :param model.movement.Movement movement: Movement in which this relationship is happening.

    :attribute leader: The leading user.
    :attribute follower: The following user.
    :attribute movement: The movement in which this connection happens.
    """

    __tablename__ = "assoc"

    id = db.Column(db.Integer, primary_key=True)
    leader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movements.id"))
    created = db.Column(db.DateTime(timezone=True))
    destroyed = db.Column(db.DateTime(timezone=True))

    movement = db.relationship("Movement", back_populates="user_associations")
    follower = db.relationship(
        "User", foreign_keys=[follower_id], back_populates="follower_associations"
    )
    leader = db.relationship("User", foreign_keys=[leader_id])

    def __init__(self, movement=None, follower=None, leader=None):
        # movement=None and follower=None
        # are required for correct functioning of
        # user_associations in ./movement.py
        self.follower = follower
        self.movement = movement
        self.leader = leader
        self.created = datetime.now()
        self.destroyed = None

    def __repr__(self):
        return f"<Association id={self.id} {self.follower}->{self.leader} in {self.movement}{'x' if self.destroyed else ''}>"

    def save_to_db(self):
        """
        Save this association to the database.
        """
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        """
        Delete this association from the database.

        :warning: This action is permanent and can not be undone.
        """
        db.session.delete(self)
        db.session.commit()

    def destroy(self):
        """
        Destroy this association.
        Association can still be found in database.
        """
        self.destroyed = datetime.now()
