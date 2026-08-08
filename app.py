from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import pandas as pd
from io import BytesIO
import math

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("schedule.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS drinks
                 (date TEXT,
                  amount REAL,
                  staff_count INTEGER)''')
    conn.commit()
    conn.close()

# 酒錢分攤首頁
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/save_drinks", methods=["POST"])
def save_drinks():
    data = request.get_json()
    conn = sqlite3.connect("schedule.db")
    c = conn.cursor()
    c.execute("DELETE FROM drinks")
    for row in data:
        c.execute("INSERT INTO drinks (date, amount, staff_count) VALUES (?, ?, ?)",
                  (row["date"], row["amount"], row["staff"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/export_drinks")
def export_drinks():
    conn = sqlite3.connect("schedule.db")
    c = conn.cursor()
    c.execute("SELECT date, amount, staff_count FROM drinks ORDER BY date")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return "目前沒有酒錢紀錄，請先填寫並送出。"

    df = pd.DataFrame(rows, columns=["Date", "Amount", "StaffCount"])
    df["Date"] = pd.to_datetime(df["Date"])
    
    

    df["PerPerson"] = df.apply(
    lambda x: math.floor(x["Amount"] / x["StaffCount"]) if x["StaffCount"] > 0 else 0,
    axis=1
)


    df["Month"] = df["Date"].dt.to_period("M")
    monthly = df.groupby("Month").agg({
        "Amount": "sum",
        "StaffCount": "sum",
        "PerPerson": "mean"
    }).reset_index()

    df["Date"] = df["Date"].dt.strftime("%m/%d/%Y")
    monthly["Month"] = monthly["Month"].astype(str)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Daily Drinks", index=False)
        monthly.to_excel(writer, sheet_name="Monthly Summary", index=False)
    output.seek(0)

    return Response(output,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition":"attachment;filename=drinks.xlsx"})

import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))  # Render 會指定 PORT
    app.run(host="0.0.0.0", port=port, debug=True)

