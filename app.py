from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
)
import sqlite3
import os
import calendar
from datetime import datetime, date
import hashlib

# ------------------------------------------------
# CONFIG FLASK
# ------------------------------------------------
app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY_D3NTAL_TECH_2025"

DB_PATH = os.path.join("db", "database.db")
SALT = "D3NTAL_TECH_SUPER_SALT_2025"  # doit être identique à init_db.py


# ------------------------------------------------
# UTILS DB & HASH
# ------------------------------------------------
def hash_password(plain_password: str) -> str:
    """
    Retourne le hash SHA256 du mot de passe avec le sel.
    """
    to_hash = (SALT + plain_password).encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()


def get_db_connection():
    """
    Retourne une connexion SQLite sur db/database.db.
    """
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_credentials(email: str, password: str) -> bool:
    """
    Vérifie que l'email existe et que le mot de passe correspond.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM authorized_users WHERE email = ?",
        (email,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    stored_hash = row["password_hash"]
    return stored_hash == hash_password(password)


# ------------------------------------------------
# ROUTE: LOGIN
# ------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if check_credentials(email, password):
            session["user"] = email
            return redirect("/calendar")
        else:
            error = "Email ou mot de passe incorrect."

    return render_template("login.html", error=error)


# ------------------------------------------------
# ROUTE: LOGOUT
# ------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------------------------------------
# ROUTE: CALENDRIER PROTÉGÉ
# ------------------------------------------------
@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect("/")

    # Date actuelle
    now = datetime.now()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))

    # Navigation mois précédent / suivant
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

    # Génération des jours du mois
    cal = calendar.Calendar(firstweekday=0)  # 0 = lundi pour Python
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


# ------------------------------------------------
# MAIN LOCAL
# ------------------------------------------------
if __name__ == "__main__":
    # Initialisation DB si nécessaire
    if not os.path.exists(DB_PATH):
        from init_db import init_db

        init_db()

    app.run(host="0.0.0.0", port=5000, debug=True)
