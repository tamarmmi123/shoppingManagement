from flask import Flask, request, send_file, render_template, redirect, url_for, session, flash, Response, render_template_string
from models import db
from models.User import User
from models.Purchase import Purchase
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import os
import numpy as np
from bs4 import BeautifulSoup



app = Flask(__name__, template_folder="templates")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shoppingManagement.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "my_secret_key"


DATABASE = "shoppingManagement.db"

CATEGORIES = ["Food", "Transport", "Clothing", "Entertainment"]

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



@app.route("/purchases", methods=["GET", "POST"])
def purchases():
    if "user_id" not in session:
        flash("You must be logged in to view purchases!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    chart = "purchases"

    if request.method == "POST":
        chart = request.form.get("chart", "purchases")

    purchases = Purchase.query.filter_by(user_id=user.id).all()
    categories = ["Food", "Transport", "Clothing", "Entertainment", "Other"]

    weekly_graph = url_for('static', filename='user_weekly_graph.png')
    category_graph = url_for('static', filename='user_category_graph.png')
    
    return render_template("purchases.html",user=user,purchases=purchases,categories=categories,chart=chart,weekly_graph=weekly_graph,category_graph=category_graph)

from datetime import datetime

@app.route('/add_purchase', methods=['POST'])
def add_purchase():
    if "user_id" not in session:
        return redirect(url_for('register')) 

    categories = ["Food", "Transport", "Clothing", "Entertainment"]
    
    category = request.form['category']
    
    if category == "Other" and request.form.get('custom_category'):
        category = request.form['custom_category'].strip()

    date_str = request.form['date'] 
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    new_purchase = Purchase(
        prodName=request.form['prodName'],
        qty=int(request.form['qty']),
        price=float(request.form['price']),
        category=category,
        date=date_obj,
        user_id=session["user_id"]
    )

    db.session.add(new_purchase)
    db.session.commit()

    return redirect(url_for('purchases'))
    
@app.route('/update_purchase/<int:id>', methods=['GET', 'POST'])
def update_purchase(id):
    if "user_id" not in session:
        return redirect(url_for('register')) 

    categories = ["Food", "Transport", "Clothing", "Entertainment"]
    purchase = Purchase.query.get_or_404(id)

    if request.method == "POST":
        category = request.form['category']
        
        if category == "Other" and request.form.get('custom_category'):
            category = request.form['custom_category'].strip()

        purchase.prodName = request.form['prodName']
        purchase.qty = int(request.form['qty'])
        purchase.price = float(request.form['price'])
        purchase.category = category
        purchase.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

        db.session.commit()
        return redirect(url_for('purchases', user_id=session["user_id"]))  

    return render_template('updatePurchase.html', 
                           purchase=purchase, 
                           categories=categories, 
                           formatted_date=purchase.date.strftime('%Y-%m-%d'))


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
    plt.savefig(output, format='png', bbox_inches='tight', transparent=True) 
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
    plt.savefig(output, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    output.seek(0)
    return Response(output.getvalue(), mimetype='image/png')

@app.route("/demoProfile", methods=["GET", "POST"])
def demo_profile():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    static_folder = os.path.join(BASE_DIR, "static")

    prodNames = ["Laptop", "Phone", "Headphones", "Monitor", "Keyboard"]
    categories = ["Electronics", "Electronics", "Accessories", "Electronics", "Accessories"]
    
    num_purchases = 10
    data = {
        "id": np.arange(1, num_purchases + 1),
        "prodName": np.random.choice(prodNames, num_purchases),
        "price": np.round(np.random.uniform(20, 1000, num_purchases), 2),
        "quantity": np.random.randint(1, 5, num_purchases),
        "category": np.random.choice(categories, num_purchases),
        "date": pd.date_range(end=pd.Timestamp.today(), periods=num_purchases).strftime('%Y-%m-%d')
    }

    df = pd.DataFrame(data)

    df["date"] = pd.to_datetime(df["date"])
    df['Week Start'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    df['Week End'] = df['date'].dt.to_period('W').apply(lambda r: r.end_time)
    df['Week Range'] = df.apply(lambda row: f"{row['Week Start'].strftime('%b %d')} - {row['Week End'].strftime('%b %d')}", axis=1)
    weekly_expenses = df.groupby('Week Range')['price'].sum()
    weekly_graph_path = os.path.join(static_folder, "weekly_graph.png")

    fig, ax = plt.subplots(figsize=(10, 6))
    weekly_expenses.plot(kind='bar', ax=ax, color='#0e9e90')
    ax.set_xlabel("Week Range")
    ax.set_ylabel("Total Spent (₪)")
    ax.set_title("Weekly Spending")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(weekly_graph_path, transparent=True)
    plt.close()

    category_totals = df.groupby("category")["price"].sum()

    category_graph_path = os.path.join(static_folder, "category_graph.png")
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%', startangle=140)
    ax.set_title("Spending by Category")
    plt.tight_layout()
    plt.savefig(category_graph_path, transparent=True)
    plt.close()

    chart = request.form.get('chart', 'purchases') 

    return render_template("demo_profile.html", 
                           chart=chart, 
                           purchases=df.to_dict(orient="records"), 
                           weekly_graph_path=weekly_graph_path, 
                           category_graph_path=category_graph_path)


@app.route('/compare_prices', methods=['POST'])
def compare_prices():
    if "user_id" not in session:
        flash("You must be logged in to view purchases!", "danger")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("logout"))

    user_purchases_query = Purchase.query.filter_by(user_id=user.id).all()
    
    user_purchases = [
        {"prodName": p.prodName, "price_paid": p.price}
        for p in user_purchases_query
    ]

    store_products_data = [
    {"prodName": "Milk", "price": 4.50},
    {"prodName": "Shampoo", "price": 10.99},
    {"prodName": "Toothpaste", "price": 7.30},
    {"prodName": "Bread", "price": 3.20},
    {"prodName": "Cheese", "price": 15.60},
    {"prodName": "Notebook", "price": 12.75},
    {"prodName": "Ballpoint Pens", "price": 6.30},
    {"prodName": "Trash Bags", "price": 14.00},
    {"prodName": "Hand Soap", "price": 5.20},
    {"prodName": "Batteries (AA)", "price": 18.90},
    {"prodName": "Sticky Notes", "price": 3.10},
    {"prodName": "Tissue Box", "price": 7.40},
    {"prodName": "Coffee Mug", "price": 16.25},
    {"prodName": "Alarm Clock", "price": 39.99}
]


    rendered_html = render_template_string(
        """
        <div id="store-products">
            {% for product in store_products %}
                <div class="product">
                    <span class="product-name">{{ product['prodName'] }}</span> -
                    <span class="product-price">{{ product['price'] }}</span>
                </div>
            {% endfor %}
        </div>
        """,
        store_products=store_products_data
    )

    soup = BeautifulSoup(rendered_html, 'html.parser')

    prodNames = [tag.text.strip() for tag in soup.find_all("span", class_="product-name")]
    product_prices = [float(tag.text.strip()) for tag in soup.find_all("span", class_="product-price")]

    store_products = [{"prodName": name, "price": price} for name, price in zip(prodNames, product_prices)]

    cheaper_products = []

    for user_purchase in user_purchases:
        for store_product in store_products:
            if store_product["prodName"].lower() == user_purchase["prodName"].lower():
                if store_product["price"] < user_purchase["price_paid"]:
                    cheaper_products.append({
                        "prodName": user_purchase["prodName"],
                        "price_paid": user_purchase["price_paid"],
                        "store_price": store_product["price"]
                    })

    return render_template('results.html', cheaper_products=cheaper_products)


if __name__ == "__main__":
    app.run(debug=True)
