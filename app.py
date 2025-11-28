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

    today = datetime.today()
    year = today.year
    month = today.month

    cal = calendar.Calendar()
    calendar_days = cal.monthdatescalendar(year, month)

    month_name = calendar.month_name[month]

    return render_template(
        "calendar.html",
        month_name=month_name,
        year=year,
        calendar_days=calendar_days
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
