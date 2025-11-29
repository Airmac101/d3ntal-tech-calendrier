from flask import Flask, render_template, request, session, redirect, flash
import os
import calendar
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cle_secrete_d3ntal_tech"

AUTHORIZED_EMAILS = [
    "denismeuret01@gmail.com",
    "denismeuret@d3ntal-tech.fr",
    "isis.stouvenel@d3ntal-tech.fr"
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")

        if email in AUTHORIZED_EMAILS:
            session["user"] = email
            return redirect("/calendar")
        else:
            flash("❌ Email non autorisé. Accès refusé.")

    return render_template("login.html")


@app.route("/calendar")
def calendar_view():
    if "user" not in session:
        return redirect("/")

    # GET parameters: /calendar?year=2025&month=11
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    today = datetime.today()

    # If no year/month provided → use today
    if not year: year = today.year
    if not month: month = today.month

    # Calendar logic
    cal = calendar.Calendar()
    calendar_days = cal.monthdatescalendar(year, month)
    month_name = calendar.month_name[month]

    # Navigation
    prev_month = month - 1
    next_month = month + 1
    prev_year = year
    next_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    if next_month == 13:
        next_month = 1
        next_year += 1

    return render_template(
        "calendar.html",
        month_name=month_name,
        year=year,
        month=month,
        calendar_days=calendar_days,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
