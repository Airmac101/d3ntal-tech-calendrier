import os
import json
import sqlite3
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    session,
    send_from_directory,
)

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

# ===============================
# DATABASE USING RENDER DISK
# ===============================
DB_PATH = "/var/data/events.db"   # <- DISQUE PERSISTANT RENDER
UPLOAD_BASE = "/var/data/uploads" # <- dossiers fichiers persistants


# ===============================
# DATABASE CONNECTION
# ===============================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===============================
# INITIALIZE DATABASE (AUTO)
# ===============================
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # TABLE EVENTS
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            event_type TEXT NOT NULL,
            collaborators TEXT,
            priority TEXT,
            notes TEXT,
            user_email TEXT
        );
        """
    )

    # Add "files" column if missing
    cur.execute("PRAGMA table_info(events);")
    columns = [row[1] for row in cur.fetchall()]
    if "files" not in columns:
        cur.execute("ALTER TABLE events ADD COLUMN files TEXT;")

    # TABLE authorized_users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        """
    )

    # DEFAULT USERS (4 ORIGIN + 2 NEW)
    default_password = "D3ntalTech!@2025"
    default_users = [
        ("denismeuret01@gmail.com", default_password),
        ("isis.stouvenel@d3ntal-tech.fr", default_password),
        ("contact@d3ntal-tech.fr", default_password),
        ("admin@d3ntal-tech.fr", default_password),
        # New accounts
        ("denismeuret@d3ntal-tech.fr", default_password),
        ("isis.42420@gmail.com", default_password),
    ]

    for email, pwd in default_users:
        cur.execute(
            """
            INSERT OR IGNORE INTO authorized_users (email, password)
            VALUES (?, ?)
            """,
            (email, pwd),
        )

    conn.commit()
    conn.close()


# ===============================
# UTILITIES
# ===============================
def ensure_upload_folder():
    os.makedirs(UPLOAD_BASE, exist_ok=True)


def event_type_to_css(event_type: str) -> str:
    lower = (event_type or "").lower()
    if "rdv" in lower or "rendez" in lower:
        return "rdv"
    if "réunion" in lower or "reunion" in lower:
        return "reunion"
    if "admin" in lower:
        return "admin"
    if "urgence" in lower:
        return "urgence"
    if "formation" in lower:
        return "formation"
    return "autre"


# ===============================
# EMAIL UTILITIES
# ===============================
def send_event_email(subject: str, html_content: str):
    """
    Envoi d'un email HTML pour les événements (création / modification / suppression).
    Utilise les variables d'environnement :
    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD.
    """
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    # Si la config SMTP est incomplète, on log et on ne plante pas l'appli
    if not smtp_server or not smtp_user or not smtp_password:
        print("EMAIL WARNING: SMTP configuration incomplete, email not sent.")
        return

    # Destinataires fixes (adaptables)
    recipients = [
        "denismeuret@d3ntal-tech.fr",
        "isis.stouvenel@d3ntal-tech.fr",
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
        print("EMAIL sent successfully.")
    except Exception as e:
        print("EMAIL ERROR:", e)


def build_event_email(
    action: str,
    title: str,
    event_date: str,
    event_time: str,
    event_type: str,
    collaborators: str,
    priority: str,
    notes: str,
    user_email: str,
) -> str:
    """
    Gabarit HTML pour les emails d'événement (style Notion-like).
    """
    collaborators = collaborators or ""
    notes = notes or ""
    priority = priority or "Normal"
    event_time = event_time or ""

    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background-color: #f7f7f7;">
        <h2 style="color:#2F80ED; margin-bottom: 10px;">{action} — D3NTAL TECH</h2>
        <p style="color:#555; margin-top:0; margin-bottom: 20px;">
            Un événement a été enregistré dans le calendrier D3NTAL TECH.
        </p>

        <table style="border-collapse: collapse; width: 100%; background-color:#fff;">
            <tr>
                <th style="text-align:left; padding:8px; border-bottom:1px solid #e0e0e0; background-color:#fafafa;">Champ</th>
                <th style="text-align:left; padding:8px; border-bottom:1px solid #e0e0e0; background-color:#fafafa;">Valeur</th>
            </tr>
            <tr><td style="padding:8px;">Titre</td><td style="padding:8px;">{title}</td></tr>
            <tr><td style="padding:8px;">Date</td><td style="padding:8px;">{event_date}</td></tr>
            <tr><td style="padding:8px;">Heure</td><td style="padding:8px;">{event_time}</td></tr>
            <tr><td style="padding:8px;">Type</td><td style="padding:8px;">{event_type}</td></tr>
            <tr><td style="padding:8px;">Collaborateurs</td><td style="padding:8px;">{collaborators}</td></tr>
            <tr><td style="padding:8px;">Priorité</td><td style="padding:8px;">{priority}</td></tr>
            <tr><td style="padding:8px;">Notes</td><td style="padding:8px; white-space:pre-wrap;">{notes}</td></tr>
            <tr><td style="padding:8px;">Créé / Modifié par</td><td style="padding:8px;">{user_email}</td></tr>
        </table>

        <p style="font-size:12px; color:#999; margin-top:20px;">
            Notification automatique D3NTAL TECH — Merci de ne pas répondre à cet e-mail.
        </p>
    </div>
    """
    return html


# ===============================
# LOGIN SYSTEM
# ===============================
@app.route("/")
def index():
    return render_template("login.html")


@app.route("/", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM authorized_users WHERE email = ? AND password = ?",
        (email, password),
    )
    user = cur.fetchone()
    conn.close()

    if user:
        session["user"] = email
        return redirect("/calendar")
    return render_template("login.html", error="Identifiants incorrects.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===============================
# CALENDAR VIEW
# ===============================
@app.route("/calendar")
def calendar_view():
    if "user" not in session:
        return redirect("/")

    today = date.today()

    import calendar

    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))
    cal = calendar.Calendar()

    weeks = cal.monthdatescalendar(year, month)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM events WHERE strftime('%Y-%m', event_date) = ?",
        (f"{year:04d}-{month:02d}",),
    )
    rows = cur.fetchall()
    conn.close()

    # --------- EVENTS BY DATE (POUR LES CASES DU CALENDRIER) ----------
    events_by_date = {}
    for r in rows:
        d_str = r["event_date"]
        if d_str not in events_by_date:
            events_by_date[d_str] = []

        files_list = []
        if r["files"]:
            try:
                files_list = json.loads(r["files"])
            except Exception:
                files_list = []

        events_by_date[d_str].append(
            {
                "id": r["id"],
                "user_email": r["user_email"],
                "title": r["title"],
                "date": r["event_date"],
                "time": r["event_time"],
                "type": r["event_type"],
                "collaborators": r["collaborators"],
                "priority": r["priority"],
                "notes": r["notes"],
                "files": files_list,
                "css_class": event_type_to_css(r["event_type"]),
            }
        )

    # --------- RÉCAPITULATIF DU MOIS (week_summary) ----------
    # week_summary est un dict : { date_iso: { "date": date_obj, "events": [ ... ] } }
    month_summary = {}
    for r in rows:
        d_iso = r["event_date"]  # ex: '2025-11-30'
        if not d_iso:
            continue
        if d_iso not in month_summary:
            try:
                date_obj = date.fromisoformat(d_iso)
            except Exception:
                continue
            month_summary[d_iso] = {"date": date_obj, "events": []}

        month_summary[d_iso]["events"].append(
            {
                "time": r["event_time"],
                "type": r["event_type"],
                "title": r["title"],
                "collab": r["collaborators"],
                "priority": r["priority"],
                "notes": r["notes"],
            }
        )

    # Dates limites pour le titre du récap
    last_day_number = calendar.monthrange(year, month)[1]
    week_start = date(year, month, 1)
    week_end = date(year, month, last_day_number)

    return render_template(
        "calendar.html",
        calendar_days=weeks,
        events_by_date=events_by_date,
        current_day=today,
        month=month,
        year=year,
        month_name=date(year, month, 1).strftime("%B").capitalize(),
        next_month=(month % 12) + 1,
        next_year=year + 1 if month == 12 else year,
        prev_month=(month - 2) % 12 + 1,
        prev_year=year - 1 if month == 1 else year,
        week_start=week_start,
        week_end=week_end,
        week_summary=month_summary,
    )


# ===============================
# API ADD EVENT
# ===============================
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"status": "error", "message": "missing title"}), 400

    event_type = data.get("event_type") or "Autre"
    event_date_str = data.get("event_date", "")
    event_time_str = data.get("event_time", "00:00")
    collaborators = data.get("collaborators", "")
    priority = data.get("priority", "Normal")
    notes = data.get("notes", "")
    user_email = session["user"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (user_email, title, event_date, event_time, event_type, collaborators, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_email,
            title,
            event_date_str,
            event_time_str,
            event_type,
            collaborators,
            priority,
            notes,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    # ------- EMAIL : NOUVEL ÉVÉNEMENT -------
    html = build_event_email(
        "Nouvel événement",
        title,
        event_date_str,
        event_time_str,
        event_type,
        collaborators,
        priority,
        notes,
        user_email,
    )
    send_event_email("D3NTAL TECH — Nouvel événement", html)

    return jsonify({"status": "success", "event_id": new_id})


# ===============================
# API UPDATE EVENT
# ===============================
@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "missing event_id"}), 400

    event_type = data.get("event_type") or "Autre"
    title = data.get("title", "").strip()
    event_date_str = data.get("event_date", "")
    event_time_str = data.get("event_time", "00:00")
    collaborators = data.get("collaborators", "")
    priority = data.get("priority", "Normal")
    notes = data.get("notes", "")
    user_email = session["user"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE events
        SET title=?, event_date=?, event_time=?, event_type=?, collaborators=?, priority=?, notes=?
        WHERE id=?
        """,
        (
            title,
            event_date_str,
            event_time_str,
            event_type,
            collaborators,
            priority,
            notes,
            event_id,
        ),
    )
    conn.commit()
    conn.close()

    # ------- EMAIL : ÉVÉNEMENT MODIFIÉ -------
    html = build_event_email(
        "Événement modifié",
        title,
        event_date_str,
        event_time_str,
        event_type,
        collaborators,
        priority,
        notes,
        user_email,
    )
    send_event_email("D3NTAL TECH — Événement modifié", html)

    return jsonify({"status": "success"})


# ===============================
# API DELETE EVENT
# ===============================
@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "missing event_id"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # On récupère l'événement avant suppression pour l'email
    cur.execute("SELECT * FROM events WHERE id=?", (event_id,))
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
            session["user"],
        )
        send_event_email("D3NTAL TECH — Événement supprimé", html)

    cur.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ===============================
# UPLOAD FILES
# ===============================
@app.route("/upload_files", methods=["POST"])
def upload_files():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    event_id = request.form.get("event_id")
    ensure_upload_folder()

    event_folder = os.path.join(UPLOAD_BASE, str(event_id))
    os.makedirs(event_folder, exist_ok=True)

    uploaded_paths = []

    if "files" in request.files:
        for f in request.files.getlist("files"):
            filename = f.filename
            final_path = os.path.join(event_folder, filename)
            f.save(final_path)
            uploaded_paths.append(f"{event_id}/{filename}")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT files FROM events WHERE id=?", (event_id,))
    row = cur.fetchone()

    existing = []
    if row and row["files"]:
        try:
            existing = json.loads(row["files"])
        except Exception:
            existing = []

    final_list = existing + uploaded_paths

    cur.execute(
        "UPDATE events SET files=? WHERE id=?",
        (json.dumps(final_list), event_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ===============================
# DOWNLOAD FILE
# ===============================
@app.route("/download_file/<path:rel_path>")
def download_file(rel_path):
    folder, filename = os.path.split(rel_path)
    return send_from_directory(
        os.path.join(UPLOAD_BASE, folder), filename, as_attachment=True
    )


# ===============================
# AUTO DB INIT AT STARTUP
# ===============================
try:
    initialize_database()
except Exception as e:
    print("Erreur lors de l'initialisation DB:", e)


# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
