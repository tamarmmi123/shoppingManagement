from flask import Flask, request, render_template, redirect, url_for, session, flash
from models import db
from models.User import User
from models.Purchase import Purchase
from datetime import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shoppingManagement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "my_secret_key"

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for("register"))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists. Please log in.", "warning")
            return redirect(url_for("login"))
        
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("purchases"))

    return render_template("register.html")


@app.route("/purchases", methods=["GET"])
def purchases():
    print("Session Data:", session)

    if "user_id" not in session:
        flash("You must be logged in to view purchases!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    
    if not user:
        print("ERROR: User not found in database!")
    else:
        print(f"Logged-in user: {user.email}")

    user_purchases = Purchase.query.filter_by(user_id=user.id).all()

    return render_template("purchases.html", user=user, purchases=user_purchases)


if __name__ == "__main__":
    app.run(debug=True)