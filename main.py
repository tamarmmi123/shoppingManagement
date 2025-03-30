from flask import Flask, request, send_file, render_template, redirect, url_for, session, flash, Response
from models import db
from models.User import User
from models.Purchase import Purchase
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shoppingManagement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "my_secret_key"


DATABASE = "shoppingManagement.db"

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error_message = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()

        if not email or not password:
            error_message = "Email and password are required!"
        elif not user or user.password != password:
            error_message = "Invalid email or password!"

        if error_message:
            return render_template("login.html", error=error_message)

        session["user_id"] = user.id
        return redirect(url_for("purchases"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    error_message = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            error_message = "Email and password are required!"
        elif User.query.filter_by(email=email).first():
            error_message = "User already exists. Please log in."
        
        if error_message:
            return render_template("register.html", error=error_message)
        
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("purchases"))

    return render_template("register.html")

@app.route("/update_password/<int:id>", methods=["GET", "POST"])
def update_password(id):
    error_message = None
    success_message = None
    
    if "user_id" not in session or session["user_id"] != id:
        error_message = "You must be logged in to add a purchase!"
        return redirect(url_for("login"))
    
    user = User.query.get(id)

    if not user:
        error_message = "User not found!"
        return redirect(url_for("purchases"))

    if request.method == "POST":
        email = request.form["email"]
        current_password = request.form["cPassword"]
        new_password = request.form["nPassword"]

        if user.email != email:
            error_message = "Email does not match!"
            return redirect(url_for("update_password", id=id))
    
        if user.password != current_password:
            error_message = "Incorrect current password!"
            return redirect(url_for("update_password", id=id))
        
        user.password = new_password
        db.session.commit()
        success_message = "Purchase updated successfully!"
        return redirect(url_for("index"))
    
    else:
        error_message = "The password is incorrect.Try again"
        return redirect(url_for("update_password", id=id))

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

    for p in user_purchases:
        print(f"Purchase: {p.prodName}, {p.qty}, {p.price}, {p.category}, {p.date}")

    return render_template("purchases.html", user=user, purchases=user_purchases)

@app.route("/add_purchase", methods=["GET", "POST"])
def add_purchase():
    error_message = None
    seccess_message = None
    if "user_id" not in session:
        error_message = "You must be logged in to add a purchase!"
        return redirect(url_for("login"))
        
    user_id = session["user_id"]
    prod_name = request.form.get("prodName")
    qty = request.form.get("qty")
    price = request.form.get("price")
    category = request.form.get("category")
    date_purchased = request.form.get("date")
    
    if not prod_name or not qty or not price or not category:
        error_message = "All fields are required!", "danger"
        return redirect(url_for("add_purchase"))

    date_obj = datetime.strptime(date_purchased, "%Y-%m-%d")

    new_purchase = Purchase(
        prodName=prod_name,
        qty=int(qty),
        price=float(price),
        category=category,
        date=date_obj,
        user_id=user_id
    )

    db.session.add(new_purchase)
    db.session.commit()

    
    seccess_message ="Purchase added successfully!"
    return redirect(url_for("purchases"))

@app.route("/update_purchase/<int:id>", methods=["GET", "POST"])
def update_purchase(id):
    error_message = None
    success_message = None
    if "user_id" not in session:
        error_message = "You must be logged in to add a purchase!"
        return redirect(url_for("login"))
    
    purchase = Purchase.query.get(id)

    if not purchase:
        error_message = "Purchase not found!"
        return redirect(url_for("purchases"))

    if request.method == "GET":
        return render_template("updatePurchase.html", purchase=purchase)

    purchase.prodName = request.form["prodName"]
    purchase.qty = int(request.form["qty"])
    purchase.price = float(request.form["price"])
    purchase.category = request.form["category"]
    purchase.date = datetime.strptime(request.form["date"], "%Y-%m-%d")

    db.session.commit()
    success_message = "Purchase updated successfully!"
    return redirect(url_for("purchases"))

@app.route("/delete_purchase/<int:id>", methods=["GET", "DELETE"])
def delete_purchase(id):
    error_message = None
    if "user_id" not in session:
        error_message = "You must be logged in to add a purchase!"
        return redirect(url_for("login"))
    
    purchase = Purchase.query.get(id)

    if not purchase:
        error_message = "Purchase not found!"
        return redirect(url_for("purchases"))
    
    db.session.delete(purchase)
    db.session.commit()
    return redirect(url_for("purchases"))

@app.route("/filter_purchases", methods=["GET"])
def filter_purchases():
    if "user_id" not in session:
        flash("You must be logged in to filter purchases!", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]
    filter_option = request.args.get("filter", "none")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Purchase.query.filter_by(user_id=user_id)

    if filter_option == "last_week":
        one_week_ago = datetime.now() - timedelta(weeks=1)
        query = query.filter(Purchase.date >= one_week_ago)

    elif filter_option == "last_year":
        one_year_ago = datetime.now() - timedelta(days=365)
        query = query.filter(Purchase.date >= one_year_ago)

    elif filter_option == "custom_range" and start_date and end_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        query = query.filter(Purchase.date.between(start_date_obj, end_date_obj))

    filtered_purchases = query.all()

    return render_template("purchases.html", purchases=filtered_purchases)



@app.route('/saveData')
def save_data():
    purchases = Purchase.query.all()
    data = [
        {"Product Name": p.prodName, "Quantity": p.qty, "Price": p.price, "category": p.category, "date": p.date}
        for p in purchases
    ]
    
    df = pd.DataFrame(data)
    file_path = "saveData.csv"
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

    return send_file(file_path, as_attachment=True)


def generate_empty_plot():
    """Creates an empty plot if no data is available."""
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "No Data Available", fontsize=12, ha='center', va='center')
    ax.set_axis_off()

    output = io.BytesIO()
    plt.savefig(output, format='png')
    plt.close(fig)
    output.seek(0)
    return Response(output.getvalue(), mimetype='image/png')

def get_purchases(user_id):
    purchases = Purchase.query.filter_by(user_id=user_id).all()
    return purchases

@app.route('/weekly-expenses')
def weekly_expenses():
    if "user_id" not in session:
        return "Unauthorized", 403

    user_id = session["user_id"]
    purchases = get_purchases(user_id)  
    
    data = [{
        'category': p.category,
        'qty': p.qty,
        'price': p.price,
        'date': p.date,
        'cost': p.qty * p.price
    } for p in purchases]
    
    df = pd.DataFrame(data)

    if df.empty:
        return generate_empty_plot()

    df['date'] = pd.to_datetime(df['date'])

    df['Week Start'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    df['Week End'] = df['date'].dt.to_period('W').apply(lambda r: r.end_time)

    df['Week Range'] = df.apply(lambda row: f"{row['Week Start'].strftime('%b %d')} - {row['Week End'].strftime('%b %d')}", axis=1)

    weekly_expenses = df.groupby('Week Range')['cost'].sum()

    fig, ax = plt.subplots(figsize=(14, 6))
    weekly_expenses.plot(kind='bar', title="Weekly Expenses", ax=ax, width=0.8)

    ax.set_ylabel('Total Cost')
    ax.set_xlabel('Week')
    ax.set_xticklabels(weekly_expenses.index, rotation=0, ha='center') 

    ax.grid(axis='y', linestyle='--', alpha=0.7)

    output = io.BytesIO()
    plt.savefig(output, format='png', bbox_inches='tight') 
    plt.close(fig)
    output.seek(0)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/category-expenses')
def category_expenses():
    """Generate a pie chart of expenses by category with a legend."""
    if "user_id" not in session:
        return "Unauthorized", 403

    user_id = session["user_id"]
    purchases = get_purchases(user_id)  
    
    data = [{
        'category': p.category,
        'qty': p.qty,
        'price': p.price,
        'date': p.date,
        'cost': p.qty * p.price
    } for p in purchases]

    df = pd.DataFrame(data)

    if df.empty:
        return generate_empty_plot()

    category_expenses = df.groupby('category')['cost'].sum()

    fig, ax = plt.subplots(figsize=(10, 6))
    wedges, texts, autotexts = ax.pie(
        category_expenses, labels=None, autopct='%1.1f%%', startangle=140
    )

    ax.legend(wedges, category_expenses.index, title="Categories", loc="center left", bbox_to_anchor=(1, 0.5))

    ax.set_title("Category Expenses")

    output = io.BytesIO()
    plt.savefig(output, format='png', bbox_inches='tight')
    plt.close(fig)
    output.seek(0)
    return Response(output.getvalue(), mimetype='image/png')




if __name__ == "__main__":
    app.run(debug=True)
