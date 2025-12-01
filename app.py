import os
import json
import sqlite3
from datetime import date
from flask import Flask, render_template, request, redirect, jsonify, session, send_from_directory, Response

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "events.db")
UPLOAD_BASE = "/var/data/uploads"


# ============================================
# DATABASE CONNECTION
# ============================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================
# INIT DATABASE (auto) — authorized_users + events + files
# ============================================
def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # EVENTS table
    cur.execute("""
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
    """)

    # Add "files" column if missing
    cur.execute("PRAGMA table_info(events);")
    columns = [row[1] for row in cur.fetchall()]
    if "files" not in columns:
        cur.execute("ALTER TABLE events ADD COLUMN files TEXT;")

    # AUTHORIZED_USERS table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # Add 4 accounts from original version
    base_password = "D3ntalTech!@2025"
    default_users = [
        ("denismeuret01@gmail.com", base_password),
        ("isis.stouvenel@d3ntal-tech.fr", base_password),
        ("contact@d3ntal-tech.fr", base_password),
        ("admin@d3ntal-tech.fr", base_password),
    ]

    for email, pwd in default_users:
        cur.execute("""
            INSERT OR IGNORE INTO authorized_users (email, password)
            VALUES (?, ?)
        """, (email, pwd))

    conn.commit()
    conn.close()


# ============================================
# UTILITIES
# ============================================
def ensure_upload_folder():
    if not os.path.exists(UPLOAD_BASE):
        os.makedirs(UPLOAD_BASE, exist_ok=True)


def event_type_to_css(event_type):
    lower = event_type.lower()
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


# ============================================
# LOGIN
# ============================================
@app.route("/")
def index():
    return render_template("login.html")


@app.route("/", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "").strip()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM authorized_users WHERE email = ? AND password = ?", (email, password))
    user = cur.fetchone()
    conn.close()

    if user:
        session["user"] = email
        return redirect("/calendar")
    else:
        return render_template("login.html", error="Identifiants incorrects.")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ============================================
# CALENDAR VIEW
# ============================================
@app.route("/calendar")
def calendar_view():
    if "user" not in session:
        return redirect("/")

    today = date.today()

    import calendar
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))
    cal = calendar.Calendar(firstweekday=0)

    weeks = cal.monthdatescalendar(year, month)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE strftime('%Y-%m', event_date) = ?", (f"{year:04d}-{month:02d}",))
    rows = cur.fetchall()
    conn.close()

    events_by_date = {}

    for r in rows:
        d = r["event_date"]
        if d not in events_by_date:
            events_by_date[d] = []

        files_list = []
        if r["files"]:
            try:
                files_list = json.loads(r["files"])
            except:
                files_list = []

        events_by_date[d].append({
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
            "css_class": event_type_to_css(r["event_type"])
        })

    last_day = date(year, month, calendar.monthrange(year, month)[1])

    return render_template(
        "calendar.html",
        calendar_days=weeks,
        events_by_date=events_by_date,
        current_day=today,
        month=month,
        year=year,
        month_name=date(year, month, 1).strftime("%B").capitalize(),
        next_month=(month % 12) + 1,
        next_year=(year + 1) if month == 12 else year,
        prev_month=(month - 2) % 12 + 1,
        prev_year=(year - 1) if month == 1 else year,
        week_start=date(year, month, 1),
        week_end=last_day,
        week_summary={}
    )


# ============================================
# ADD EVENT
# ============================================
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"status": "error", "message": "missing title"}), 400

    event_date = data.get("event_date", "")
    event_time = data.get("event_time", "00:00")
    event_type = data.get("event_type") or "Autre"
    collaborators = data.get("collaborators", "")
    priority = data.get("priority", "Normal")
    notes = data.get("notes", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (user_email, title, event_date, event_time, event_type, collaborators, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session["user"], title, event_date, event_time, event_type, collaborators, priority, notes))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"status": "success", "event_id": new_id})


# ============================================
# UPDATE EVENT
# ============================================
@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)
    event_id = data.get("event_id")

    event_type = data.get("event_type") or "Autre"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE events
        SET title=?, event_date=?, event_time=?, event_type=?, collaborators=?, priority=?, notes=?
        WHERE id=?
    """, (
        data.get("title", "").strip(),
        data.get("event_date", ""),
        data.get("event_time", "00:00"),
        event_type,
        data.get("collaborators", ""),
        data.get("priority", "Normal"),
        data.get("notes", ""),
        event_id
    ))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ============================================
# DELETE EVENT
# ============================================
@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)
    event_id = data.get("event_id")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ============================================
# UPLOAD FILES
# ============================================
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
        except:
            existing = []

    final_list = existing + uploaded_paths

    cur.execute("UPDATE events SET files=? WHERE id=?", (json.dumps(final_list), event_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# ============================================
# DOWNLOAD FILE
# ============================================
@app.route("/download_file/<path:rel_path>")
def download_file(rel_path):
    folder, filename = os.path.split(rel_path)
    return send_from_directory(os.path.join(UPLOAD_BASE, folder), filename, as_attachment=True)


# ============================================
# AUTO DB INIT AT STARTUP
# ============================================
try:
    initialize_database()
except Exception as e:
    print("Erreur lors de l'initialisation DB:", e)


# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
