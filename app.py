from flask import Flask, render_template, request, session, redirect
import sqlite3
import calendar
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cle_secrete_par_defaut"

DB_NAME = "calendar.db"


# ---------------- DATABASE ----------------

def get_db():
    return sqlite3.connect(DB_NAME)


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/calendar")
        else:
            error = "Identifiants invalides"
    return render_template("login.html", error=error)


@app.route("/calendar", methods=["GET", "POST"])
def calendar_view():
    if "user" not in session:
        return redirect("/login")

    # Get the current month and year, or from the URL arguments
    today = datetime.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    month_name = calendar.month_name[month]

    # Navigate between months
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year

    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    # Get the days of the month and check for events
    cal = calendar.monthcalendar(year, month)

    calendar_days = []
    for week in cal:
        for day in week:
            if day == 0:
                calendar_days.append({"day": None, "has_event": False})
            else:
                date_key = f"{year}-{month:02d}-{day:02d}"
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM appointments WHERE date = ?", (date_key,))
                events = cur.fetchall()
                has_event = len(events) > 0
                calendar_days.append({
                    "day": day,
                    "has_event": has_event
                })

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_name=month_name,
        calendar_days=calendar_days,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
