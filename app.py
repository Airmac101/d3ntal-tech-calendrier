from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
)
import sqlite3
import os
import calendar
from datetime import datetime, date, timedelta
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ------------------------------------------------
# CONFIG FLASK
# ------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "SUPER_SECRET_KEY_D3NTAL_TECH_2025")

DB_PATH = os.path.join("db", "database.db")
SALT = "D3NTAL_TECH_SUPER_SALT_2025"


# ------------------------------------------------
# EMAIL — UTILITAIRE GLOBAL
# ------------------------------------------------
def send_event_email(subject: str, html_content: str):
    """
    Envoie un email HTML aux destinataires fixes.
    SMTP Gmail configuré dans Render.
    """

    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    recipients = [
        "denismeuret@d3ntal-tech.fr",
        "isis.stouvenel@d3ntal-tech.fr"
    ]

    msg = MIMEMultipart("alternative")
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.quit()
    except Exception as e:
        print("EMAIL ERROR:", e)


# ------------------------------------------------
# EMAIL — TEMPLATES HTML
# ------------------------------------------------
def build_event_email(action, title, event_date, event_time, event_type, collaborators, priority, notes, user_email):
    """
    Crée un email HTML Notion-like.
    """

    html = f"""
    <div style="font-family: Arial, sans-serif; padding:20px;">
        <h2 style="color:#2F80ED;">{action} — D3NTAL TECH</h2>

        <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
            <tr><th style="text-align:left; padding:8px; border-bottom:1px solid #ccc;">Champ</th>
                <th style="text-align:left; padding:8px; border-bottom:1px solid #ccc;">Valeur</th></tr>

            <tr><td style="padding:8px;">Titre</td><td>{title}</td></tr>
            <tr><td style="padding:8px;">Date</td><td>{event_date}</td></tr>
            <tr><td style="padding:8px;">Heure</td><td>{event_time}</td></tr>
            <tr><td style="padding:8px;">Type</td><td>{event_type}</td></tr>
            <tr><td style="padding:8px;">Collaborateurs</td><td>{collaborators}</td></tr>
            <tr><td style="padding:8px;">Priorité</td><td>{priority}</td></tr>
            <tr><td style="padding:8px;">Notes</td><td>{notes}</td></tr>
            <tr><td style="padding:8px;">Créé / Modifié par</td><td>{user_email}</td></tr>
        </table>
    </div>
    """

    return html
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
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS authorized_users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            event_type TEXT NOT NULL,
            collaborators TEXT,
            priority TEXT DEFAULT 'Normal',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    try:
        cur.execute("ALTER TABLE events ADD COLUMN priority TEXT DEFAULT 'Normal';")
    except:
        pass

    try:
        cur.execute("ALTER TABLE events ADD COLUMN notes TEXT DEFAULT '';")
    except:
        pass

    pwd_hash = hash_password("D3ntalTech!@2025")
    authorized_emails = [
        "denismeuret01@gmail.com",
        "isis.stouvenel@d3ntal-tech.fr",
        "isis.42420@gmail.com",
        "denismeuret@d3ntal-tech.fr",
    ]

    for email in authorized_emails:
        cur.execute(
            """
            INSERT OR REPLACE INTO authorized_users (email, password_hash)
            VALUES (?, ?);
            """,
            (email, pwd_hash),
        )

    conn.commit()
    conn.close()


def check_credentials(email: str, password: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash FROM authorized_users WHERE email = ?",
        (email,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return False
    return row["password_hash"] == hash_password(password)


def event_type_to_css(event_type: str) -> str:
    t = (event_type or "").lower()
    if "rendez" in t or "client" in t:
        return "rdv"
    if "fournisseur" in t:
        return "rdv"
    if "réunion" in t or "reunion" in t:
        return "reunion"
    if "admin" in t:
        return "admin"
    if "urgence" in t:
        return "urgence"
    if "forma" in t:
        return "formation"
    return "autre"
# ------------------------------------------------
# LOGIN / LOGOUT
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------------------------------------
# PAGE CALENDRIER
# ------------------------------------------------
@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect("/")

    now = datetime.now()
    today = date.today()

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

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM events
        WHERE substr(event_date,1,4)=?
        AND substr(event_date,6,2)=?
        ORDER BY event_date,event_time;
        """,
        (str(year), f"{month:02d}"),
    )
    rows = cur.fetchall()

    events_by_date = {}
    for r in rows:
        key = r["event_date"]
        if key not in events_by_date:
            events_by_date[key] = []
        events_by_date[key].append(
            {
                "id": r["id"],
                "title": r["title"],
                "date": r["event_date"],
                "time": r["event_time"],
                "type": r["event_type"],
                "priority": r["priority"],
                "notes": r["notes"],
                "collaborators": r["collaborators"] or "",
                "css_class": event_type_to_css(r["event_type"]),
            }
        )

    month_summary = {}
    for r in rows:
        d_iso = r["event_date"]
        if d_iso not in month_summary:
            month_summary[d_iso] = {
                "date": date.fromisoformat(d_iso),
                "events": []
            }
        month_summary[d_iso]["events"].append({
            "time": r["event_time"],
            "type": r["event_type"],
            "title": r["title"],
            "collab": r["collaborators"],
            "priority": r["priority"],
            "notes": r["notes"],
        })

    conn.close()

    month_start = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)

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
        current_day=today,
        events_by_date=events_by_date,
        week_summary=month_summary,
        week_start=month_start,
        week_end=month_end,
    )


# ------------------------------------------------
# API EVENTS (+ EMAIL)
# ------------------------------------------------
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    event_date = data.get("event_date")
    event_time = data.get("event_time")
    event_type = data.get("event_type")
    collaborators = (data.get("collaborators") or "").strip()
    priority = (data.get("priority") or "Normal").strip()
    notes = (data.get("notes") or "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (user_email,title,event_date,event_time,event_type,collaborators,priority,notes)
        VALUES (?,?,?,?,?,?,?,?);
        """,
        (session["user"], title, event_date, event_time, event_type, collaborators, priority, notes),
    )
    conn.commit()
    conn.close()

    html = build_event_email("Nouvel événement", title, event_date, event_time, event_type, collaborators, priority, notes, session["user"])
    send_event_email("D3NTAL TECH — Nouvel événement", html)

    return jsonify({"status": "success"})


@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json() or {}
    event_id = data.get("event_id")

    if not event_id:
        return jsonify({"status": "error"}), 400

    title = (data.get("title") or "").strip()
    event_date = data.get("event_date")
    event_time = data.get("event_time")
    event_type = data.get("event_type")
    collaborators = (data.get("collaborators") or "").strip()
    priority = (data.get("priority") or "Normal").strip()
    notes = (data.get("notes") or "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE events
        SET title=?,event_date=?,event_time=?,event_type=?,collaborators=?,priority=?,notes=?
        WHERE id=? AND user_email=?;
        """,
        (title, event_date, event_time, event_type, collaborators, priority, notes, event_id, session["user"]),
    )
    conn.commit()
    conn.close()

    html = build_event_email("Événement modifié", title, event_date, event_time, event_type, collaborators, priority, notes, session["user"])
    send_event_email("D3NTAL TECH — Événement modifié", html)

    return jsonify({"status": "success"})


@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json() or {}
    event_id = data.get("event_id")

    if not event_id:
        return jsonify({"status": "error"}), 400

    # On récupère l'événement avant suppression pour l’email
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id=? AND user_email=?", (event_id, session["user"]))
    row = cur.fetchone()

    if row:
        html = build_event_email(
            "Événement supprimé",
            row["title"],
            row["event_date"],
            row["event_time"],
            row["event_type"],
            row["collaborators"],
            row["priority"],
            row["notes"],
            session["user"]
        )
        send_event_email("D3NTAL TECH — Événement supprimé", html)

    cur.execute(
        "DELETE FROM events WHERE id=? AND user_email=?;",
        (event_id, session["user"]),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ------------------------------------------------
# MAIN LOCAL + RENDER
# ------------------------------------------------
if __name__ == "__main__":
    force_init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

force_init_db()
