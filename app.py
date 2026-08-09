from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import pandas as pd
from io import BytesIO

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("schedule.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS drinks
                 (date TEXT,
                  amount REAL,
                  staff_count INTEGER,
                  names TEXT)''')   # 新增 names 欄位
    conn.commit()
    conn.close()

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
        total_amount = sum(row.get("amounts", []))  # 計算酒錢小計
        staff = int(row.get("staff", 0))
        names = ", ".join(row.get("names", [])) if row.get("names") else ""
        c.execute("INSERT INTO drinks (date, amount, staff_count, names) VALUES (?, ?, ?, ?)",
                  (row["date"], total_amount, staff, names))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/export_drinks")
def export_drinks():
    conn = sqlite3.connect("schedule.db")
    c = conn.cursor()
    c.execute("SELECT date, amount, staff_count, names FROM drinks ORDER BY date")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return "目前沒有酒錢紀錄，請先填寫並送出。"

    df = pd.DataFrame(rows, columns=["日期", "酒錢總計", "上班人數", "員工名字"])
    df["每人分到"] = df.apply(
    lambda x: (x["酒錢總計"] / x["上班人數"]) if x["上班人數"] > 0 else 0,
    axis=1
)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="酒錢紀錄", index=False)
    output.seek(0)

    return Response(output,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition":"attachment;filename=drinks.xlsx"})

import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))   # Render 會自動提供 PORT
    app.run(host="0.0.0.0", port=port)

