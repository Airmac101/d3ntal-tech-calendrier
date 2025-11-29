from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify
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
SALT = "D3NTAL_TECH_SUPER_SALT_2025"


# ------------------------------------------------
# UTILS DB & HASH
# ------------------------------------------------
def hash_password(plain_password: str) -> str:
    to_hash = (SALT + plain_password).encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()


def get_db_connection():
    os.makedirs("db", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def force_init_db():
    """
    Force l'initialisation de la DB à chaque démarrage
    (nécessaire pour Render).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # ------------------------------------------------
    # Table utilisateurs autorisés
    # ------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ------------------------------------------------
    # Table des événements
    # (on la recrée pour ajouter les nouveaux champs, y compris l'heure)
    # ------------------------------------------------
    cursor.execute("DROP TABLE IF EXISTS events;")
    cursor.execute("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            event_type TEXT NOT NULL,
            collaborators TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Mot de passe unique hashé
    pwd_hash = hash_password("D3ntalTech!@2025")

    authorized_emails = [
        "denismeuret01@gmail.com",
        "isis.stouvenel@d3ntal-tech.fr",
        "isis.42420@gmail.com",
        "denismeuret@d3ntal-tech.fr",
    ]

    for email in authorized_emails:
        cursor.execute("""
            INSERT OR REPLACE INTO authorized_users (email, password_hash)
            VALUES (?, ?);
        """, (email, pwd_hash))

    conn.commit()
    conn.close()


def check_credentials(email: str, password: str) -> bool:
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

    return row["password_hash"] == hash_password(password)


# ------------------------------------------------
# ROUTE LOGIN
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
# LOGOUT
# ------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------------------------------------
# CALENDAR (PROTÉGÉ)
# ------------------------------------------------
@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect("/")

    now = datetime.now()
    year = int(request.args.get("year", now.year))
    month = int(request.args.get("month", now.month))

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

    cal = calendar.Calendar(firstweekday=0)
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
# API : AJOUT D'ÉVÉNEMENT (AJAX)
# ------------------------------------------------
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error", "message": "Non autorisé"}), 403

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    event_date = data.get("event_date") or ""
    event_time = (data.get("event_time") or "").strip()
    event_type = (data.get("event_type") or "").strip()
    collaborators = (data.get("collaborators") or "").strip()

    if not title or not event_date or not event_time or not event_type:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (user_email, title, event_date, event_time, event_type, collaborators)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (session["user"], title, event_date, event_time, event_type, collaborators))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"}), 200


# ------------------------------------------------
# MAIN LOCAL + RENDER
# ------------------------------------------------
if __name__ == "__main__":
    force_init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

# IMPORTANT : Render ignore "__main__"
# DONC on force l’init dès l'import !
force_init_db()
