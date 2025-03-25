from main import app, db
from models.User import User
from models.Purchase import Purchase
from datetime import datetime

def seed_database():
    with app.app_context():
        db.create_all()
        users = [
            User(email="sara@gmail.com", password="pass123"),
            User(email="rivkd@gmail.com", password="secure456"),
            User(email="rachel@gmail.com", password="hello789"),
            User(email="leah@gmail.com", password="mypass0")
        ]
        db.session.add_all(users)

        purchases = [
                Purchase(prodName="milk", qty=3, price=6, category="food", date=datetime.now(), user_id=users[0].id),
                Purchase(prodName="flour", qty=2, price=10.9, category="food", date=datetime.now(), user_id=users[1].id),
                Purchase(prodName="shoes", qty=3, price=179.99, category="Fashion", date=datetime.now(), user_id=users[2].id)
            ]
        db.session.add_all(purchases)
        
        db.session.commit()