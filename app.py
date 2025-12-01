from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
    Response,
    send_from_directory,
)
import sqlite3
import os
import calendar
from datetime import datetime, date, timedelta
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from werkzeug.utils import secure_filename
from io import StringIO
import csv

# ------------------------------------------
# CONFIG FLASK
# ------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "SUPER_SECRET_KEY_D3NTAL_TECH_2025")

# IMPORTANT : base PERSISTANTE sur Render
DB_PATH = "/var/data/database.db"
SALT = "D3NTAL_TECH_SUPER_SALT_2025"


# -----
# EMAIL — UTILITAIRE GLOBAL
# -----
def send_event_email(subject: str, html_content: str):
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")

    recipients = [
        "denismeuret@d3ntal-tech.fr",
        "isis.stouvenel@d3ntal-tech.fr",
    ]

    if not smtp_server or not smtp_user or not smtp_password:
        print("EMAIL WARNING: SMTP configuration incomplete, email not sent.")
        return

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
        print(f"EMAIL ERROR: {e}")


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


# ------------------------------------------------
# UTILS
# ------------------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()


def get_db_connection():
    os.makedirs("/var/data", exist_ok=True)
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
            files TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Ajout colonnes si absentes
    try:
        cur.execute("ALTER TABLE events ADD COLUMN priority TEXT DEFAULT 'Normal';")
    except:
        pass
    try:
        cur.execute("ALTER TABLE events ADD COLUMN notes TEXT DEFAULT '';")
    except:
        pass
    try:
        cur.execute("ALTER TABLE events ADD COLUMN files TEXT;")
    except:
        pass

    # Comptes autorisés
    pwd = hash_password("D3ntalTech!@2025")
    for email in [
        "denismeuret01@gmail.com",
        "isis.stouvenel@d3ntal-tech.fr",
        "isis.42420@gmail.com",
        "denismeuret@d3ntal-tech.fr",
    ]:
        cur.execute(
            "INSERT OR REPLACE INTO authorized_users (email,password_hash) VALUES (?,?)",
            (email, pwd),
        )

    conn.commit()
    conn.close()


def check_credentials(email: str, password: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM authorized_users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    return row and row["password_hash"] == hash_password(password)


def event_type_to_css(event_type: str) -> str:
    t = (event_type or "").lower()
    if "rendez" in t:
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
# ROUTES LOGIN
# ------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect("/calendar")

    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if check_credentials(email, password):
            session["user"] = email
            return redirect("/calendar")
        else:
            error = "Identifiants incorrects."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------------------------------------
# CALENDRIER
# ------------------------------------------------
@app.route("/calendar")
def calendar_view():
    if "user" not in session:
        return redirect("/")

    today = date.today()
    year = request.args.get("year", default=today.year, type=int)
    month = request.args.get("month", default=today.month, type=int)

    month_days = []
    cal = calendar.Calendar(firstweekday=0)
    for week in cal.monthdatescalendar(year, month):
        month_days.append(week)

    month_name = calendar.month_name[month]

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id,user_email,title,event_date,event_time,event_type,
               collaborators,priority,notes
        FROM events
        WHERE strftime('%Y', event_date) = ?
          AND strftime('%m', event_date) = ?
        ORDER BY event_date, event_time, title;
        """,
        (str(year), f"{month:02d}"),
    )
    rows = cur.fetchall()

    events_by_date = {}
    for r in rows:
        d = r["event_date"]
        if d not in events_by_date:
            events_by_date[d] = []
        events_by_date[d].append(
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
                "css_class": event_type_to_css(r["event_type"]),
            }
        )

    # Récap mensuel
    last_day = calendar.monthrange(year, month)[1]
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    cur.execute(
        """
        SELECT event_date,event_time,event_type,
               collaborators,priority,notes,title
        FROM events
        WHERE event_date BETWEEN ? AND ?
        ORDER BY event_date,event_time,title;
        """,
        (month_start.isoformat(), month_end.isoformat()),
    )
    recaps = cur.fetchall()
    conn.close()

    month_summary = {}
    for r in recaps:
        d = r["event_date"]
        if d not in month_summary:
            month_summary[d] = {
                "date": datetime.strptime(d, "%Y-%m-%d").date(),
                "events": [],
            }
        month_summary[d]["events"].append(
            {
                "time": r["event_time"],
                "type": r["event_type"],
                "collab": r["collaborators"],
                "priority": r["priority"],
                "notes": r["notes"],
                "title": r["title"],
            }
        )

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
# EXPORT RÉCAPITULATIF JOUR (DATE SYSTÈME)
# ------------------------------------------------
@app.route("/export_today")
def export_today():
    """
    Exporte en CSV tous les événements dont la date d'événement
    correspond à la date système (aujourd'hui).
    """
    if "user" not in session:
        return redirect("/")

    today_iso = date.today().isoformat()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT title, event_date, event_time, event_type,
               collaborators, priority, notes, user_email
        FROM events
        WHERE event_date = ?
        ORDER BY event_time, title;
        """,
        (today_iso,),
    )
    rows = cur.fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output, delimiter=";")

    # En-têtes
    writer.writerow(
        [
            "Titre",
            "Date événement",
            "Heure",
            "Type",
            "Collaborateurs",
            "Priorité",
            "Notes",
            "Créé / modifié par",
        ]
    )

    for r in rows:
        writer.writerow(
            [
                r["title"],
                r["event_date"],
                r["event_time"],
                r["event_type"],
                r["collaborators"] or "",
                r["priority"] or "",
                (r["notes"] or "").replace("\n", " ").replace("\r", " "),
                r["user_email"] or "",
            ]
        )

    csv_content = output.getvalue()
    filename = f"recap_{today_iso}.csv"

    response = Response(csv_content, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# ------------------------------------------------
# UPLOAD & TÉLÉCHARGEMENT DE FICHIERS JOINTS
# ------------------------------------------------
@app.route("/upload_files", methods=["POST"])
def upload_files():
    """
    Téléverse plusieurs fichiers et les rattache à un événement existant.
    Les chemins sont stockés en JSON dans la colonne 'files' de la table events.
    """
    if "user" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    event_id = request.form.get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "event_id manquant"}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"status": "error", "message": "Aucun fichier reçu"}), 400

    upload_root = "/var/data/uploads"
    os.makedirs(upload_root, exist_ok=True)
    event_dir = os.path.join(upload_root, f"event_{event_id}")
    os.makedirs(event_dir, exist_ok=True)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT files FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()

    existing_files = []
    if row and row["files"]:
        try:
            existing_files = json.loads(row["files"])
        except Exception:
            existing_files = []

    saved_paths = []
    for f in files:
        if not f or not f.filename:
            continue

        filename = secure_filename(f.filename)
        base, ext = os.path.splitext(filename)
        filepath = os.path.join(event_dir, filename)
        counter = 1

        while os.path.exists(filepath):
            filename = f"{base}_{counter}{ext}"
            filepath = os.path.join(event_dir, filename)
            counter += 1

        f.save(filepath)
        rel_path = os.path.relpath(filepath, upload_root)
        saved_paths.append(rel_path)

    all_files = existing_files + saved_paths

    cur.execute(
        "UPDATE events SET files = ? WHERE id = ?",
        (json.dumps(all_files), event_id),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "files": all_files})


@app.route("/download_file/<path:rel_path>")
def download_file(rel_path):
    """
    Télécharge un fichier joint à partir du chemin relatif enregistré en base.
    """
    if "user" not in session:
        return redirect("/")

    upload_root = "/var/data/uploads"
    safe_path = os.path.normpath(rel_path)
    if safe_path.startswith(".."):
        return jsonify({"status": "error", "message": "Chemin invalide"}), 400

    return send_from_directory(upload_root, safe_path, as_attachment=True)


# ------------------------------------------------
# API EVENTS + EMAILS
# ------------------------------------------------
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    event_date = data.get("event_date") or ""
    event_time = data.get("event_time") or ""
    event_type = data.get("event_type") or ""
    collaborators = data.get("collaborators") or ""
    priority = data.get("priority") or "Normal"
    notes = data.get("notes") or ""

    if not title or not event_date:
        return jsonify({"status": "error", "message": "Titre et date requis"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (user_email,title,event_date,event_time,event_type,collaborators,priority,notes)
        VALUES (?,?,?,?,?,?,?,?);
        """,
        (
            session["user"],
            title,
            event_date,
            event_time,
            event_type,
            collaborators,
            priority,
            notes,
        ),
    )
    conn.commit()
    event_id = cur.lastrowid
    conn.close()

    html = build_event_email(
        "Nouvel événement",
        title,
        event_date,
        event_time,
        event_type,
        collaborators,
        priority,
        notes,
        session["user"],
    )
    send_event_email("D3NTAL TECH — Nouvel événement", html)

    return jsonify({"status": "success", "event_id": event_id})


@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json() or {}
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "event_id manquant"}), 400

    title = (data.get("title") or "").strip()
    event_date = data.get("event_date") or ""
    event_time = data.get("event_time") or ""
    event_type = data.get("event_type") or ""
    collaborators = data.get("collaborators") or ""
    priority = data.get("priority") or "Normal"
    notes = data.get("notes") or ""

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE events
           SET title=?,
               event_date=?,
               event_time=?,
               event_type=?,
               collaborators=?,
               priority=?,
               notes=?
         WHERE id=?;
        """,
        (
            title,
            event_date,
            event_time,
            event_type,
            collaborators,
            priority,
            notes,
            event_id,
        ),
    )
    conn.commit()
    conn.close()

    html = build_event_email(
        "Événement mis à jour",
        title,
        event_date,
        event_time,
        event_type,
        collaborators,
        priority,
        notes,
        session["user"],
    )
    send_event_email("D3NTAL TECH — Événement mis à jour", html)

    return jsonify({"status": "success"})


@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json() or {}
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "event_id manquant"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT title,event_date,event_time,event_type,collaborators,priority,notes,user_email FROM events WHERE id=?", (event_id,))
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
            row["user_email"],
        )
        send_event_email("D3NTAL TECH — Événement supprimé", html)

    cur.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ------------------------------------------------
# MAIN
# ------------------------------------------------
if __name__ == "__main__":
    force_init_db()
    app.run(debug=True)

force_init_db()
