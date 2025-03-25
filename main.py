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
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Email and password are required!", "danger")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()

        if user:
            print(f"Stored password: {user.password}")
            print(f"Entered password: {password}")

        if user and user.password == password:
            session["user_id"] = user.id
            session.permanent = True
            flash("Login successful!", "success")
            return redirect(url_for("add_purchase"))
        else:
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))

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

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out!", "info")
    return redirect(url_for("index"))

@app.route("/purchases", methods=["GET"])
def purchases():
    if "user_id" not in session:
        flash("You must be logged in to view purchases!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    user_purchases = Purchase.query.filter_by(user_id=user.id).all()

    return render_template("purchases.html", user=user, purchases=user_purchases)

@app.route("/add_purchase", methods=["GET", "POST"])
def add_purchase():
    if "user_id" not in session:
        flash("You must be logged in to add a purchase!", "danger")
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    prod_name = request.form.get("prodName")
    qty = request.form.get("qty")
    price = request.form.get("price")
    category = request.form.get("category")
    
    if not prod_name or not qty or not price or not category:
        flash("All fields are required!", "danger")
        return redirect(url_for("add_purchase"))

    new_purchase = Purchase(
        prodName=prod_name,
        qty=int(qty),
        price=float(price),
        category=category,
        user_id=user_id
    )

    db.session.add(new_purchase)
    db.session.commit()

    flash("Purchase added successfully!", "success")
    return redirect(url_for("purchases"))


if __name__ == "__main__":
    app.run(debug=True)