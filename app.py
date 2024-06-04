from flask import Flask, render_template, request,jsonify
from pymongo import MongoClient
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import defaultdict
import os
app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb+srv://pradeepmajji42:Pradeep123@cluster0.mb8pytv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["dashboard"]
collection1 = db["paynow"]
collection2 = db["paylater"]


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    email = request.form["email"]
    amount = request.form["amount"]
    option = request.form["option"]
    date = request.form.get("date")

    if option == "pay_later":
        payment_data = {"email": email, "amount": amount, "date": date}
        collection2.insert_one(payment_data)

    else:
        payment_data = {"email": email, "amount": amount}
        collection1.insert_one(payment_data)

    return "Payment submitted successfully!"

@app.route("/get_list")
def get_list():
    return render_template("retrive.html")

@app.route("/retrieve", methods=["POST"])
def retrieve():
    email = request.form["email"]
    pay_now_total = collection1.aggregate([
        {"$match": {"email": email}},
        {"$group": {"_id": None, "total": {"$sum": {"$toDouble": "$amount"}}}}
    ])

    pay_later_total = collection2.aggregate([
        {"$match": {"email": email}},
        {"$group": {"_id": None, "total": {"$sum": {"$toDouble": "$amount"}}}}
    ])

    pay_now_sum = next(iter(pay_now_total), {}).get("total", 0)
    pay_later_sum = next(iter(pay_later_total), {}).get("total", 0)

    current_month = datetime.now().month
    month_totals = defaultdict(float)

    for payment in collection2.find({"email": email}):
        payment_date_str = payment["date"]
        payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d")
        payment_month = payment_date.month
        payment_amount = float(payment["amount"])
        if current_month <= payment_month <= current_month + 2:
            month_totals[payment_month] += payment_amount

    response_data = {
        "total_pay_now": pay_now_sum,
        "total_pay_later": pay_later_sum,
        "monthly_totals": dict(month_totals)
    }
    return jsonify(response_data)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
