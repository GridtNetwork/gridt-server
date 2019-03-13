from gridt.db import db


class Update(db.Model):
    """
    Representation of updates in the database.

    :attribute leader: The leader that created this update.
    :attribute movement: The movement that this update was created in.
    """

    __tablename__ = "updates"
    id = db.Column(db.Integer, primary_key=True)
    leader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movements.id"))

    leader = db.relationship("User")
    movement = db.relationship("Movement")

    def __init__(self, leader, movement):
        self.leader = leader
        self.movement = movement

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
