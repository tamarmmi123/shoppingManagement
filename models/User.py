from models import db
from models.Purchase import Purchase

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    purchases = db.relationship("Purchase", backref="user", lazy=True)
