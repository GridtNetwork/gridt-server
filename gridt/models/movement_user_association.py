from db import db


class MovementUserAssociation(db.Model):
    __tablename__ = "assoc"

    id = db.Column(db.Integer, primary_key=True)
    leader_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    movement_id = db.Column(db.Integer, db.ForeignKey("movements.id"))

    movement = db.relationship("Movement", back_populates="user_associations")
    follower = db.relationship(
        "User", foreign_keys=[follower_id], back_populates="follower_associations"
    )
    leader = db.relationship("User", foreign_keys=[leader_id])

    def __init__(self, movement, follower, leader=None):
        self.movement = movement
        self.follower = follower

    def __repr__(self):
        return (
            f"<Association id={self.id} follower={self.follower} leader={self.leader}>"
        )

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.add(self)
        db.session.commit()
