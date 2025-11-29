from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
import calendar
from datetime import datetime, date
import subprocess

# ---------------------------------------------------------
# AUTO-INIT DATABASE (exécute init_db.py automatiquement)
# ---------------------------------------------------------
try:
    subprocess.run(["python3", "init_db.py"], check=False)
except:
    pass
# ---------------------------------------------------------

app = Flask(__name__)
app.secret_key = "supersecretkey123"


# ---------------------------------------------------------
# Helper: connexion DB
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect("db/database.db")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# PAGE LOGIN
# ---------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

        if user:
            session["user"] = email
            return redirect("/calendar")
        else:
            flash("Email non autorisé.", "error")

    return render_template("login.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------------------------------------------------
# PAGE CALENDAR (PROTÉGÉE)
# ---------------------------------------------------------
@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect("/")

    # paramètres mois/année
    now = datetime.now()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))

    # calcul mois précédent / suivant
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    # génération calendrier
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(year, month)

    month_name = calendar.month_name[month]

    return render_template(
        "calendar.html",
        calendar_days=month_days,
        month=month,
        year=year,
        month_name=month_name,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        current_day=date.today(),
    )


# ---------------------------------------------------------
# RUN LOCAL (Render utilise gunicorn)
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
