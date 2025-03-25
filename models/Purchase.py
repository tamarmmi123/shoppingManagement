from models import db
from datetime import datetime


class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prodName = db.Column(db.String, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    