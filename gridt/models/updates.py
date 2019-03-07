from db import db


class Update(db.Model):
    __tablename__ = "updates"
    id = db.Column(db.Integer, primary_key=True)
    leader = db.Column(db.Integer, db.ForeignKey("users.id"))
    movement = db.Column(db.Integer, db.ForeignKey("movements.id"))

    def __init__(self, leader, movement):
        self.leader = leader
        self.movement = movement
