import os
import json
import sqlite3
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, jsonify, session, send_from_directory, Response

app = Flask(__name__)
app.secret_key = "CHANGE_ME"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_BASE = "/var/data/uploads"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    row = cur.fetchone()
    conn.close()

    if row:
        session["user"] = email
        return redirect("/calendar")
    else:
        return render_template("login.html", error="Identifiants incorrects.")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

def force_init_db():
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE events ADD COLUMN files TEXT;")
    except:
        pass
    conn.commit()
    conn.close()

force_init_db()

@app.route("/calendar")
def calendar_view():
    if "user" not in session:
        return redirect("/")

    today = date.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    import calendar
    cal = calendar.Calendar(firstweekday=0)

    weeks = []
    for week in cal.monthdatescalendar(year, month):
        weeks.append(week)

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

    import datetime
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    return render_template(
        "calendar.html",
        calendar_days=weeks,
        events_by_date=events_by_date,
        current_day=today,
        month=month,
        year=year,
        month_name=first_day.strftime("%B").capitalize(),
        next_month=(month + 1) if month < 12 else 1,
        next_year=(year + 1) if month == 12 else year,
        prev_month=(month - 1) if month > 1 else 12,
        prev_year=(year - 1) if month == 1 else year,
        week_start=first_day,
        week_end=last_day,
        week_summary={}  # recap is hidden; can reactivate later
    )

# ============================
#  API : ADD EVENT
# ============================
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error", "message": "unauthorized"}), 403

    data = request.get_json(force=True)

    title = data.get("title", "").strip()
    if not title:
        return jsonify({"status": "error", "message": "Missing title"}), 400

    event_date = data.get("event_date", "").strip()
    if not event_date:
        return jsonify({"status": "error"}), 400

    event_time = data.get("event_time", "00:00").strip()
    event_type = data.get("event_type") or ""

    # ✔ Correction appliquée ici
    if not event_type.strip():
        event_type = "Autre"

    collaborators = data.get("collaborators") or ""
    priority = data.get("priority") or "Normal"
    notes = data.get("notes") or ""

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

# ============================
#  API : UPDATE EVENT
# ============================
@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"status": "error"}), 400

    title = data.get("title", "").strip()
    event_date = data.get("event_date", "")
    event_time = data.get("event_time", "00:00")

    event_type = data.get("event_type") or ""

    # ✔ Correction appliquée ici
    if not event_type.strip():
        event_type = "Autre"

    collaborators = data.get("collaborators", "")
    priority = data.get("priority", "Normal")
    notes = data.get("notes", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE events
        SET title=?, event_date=?, event_time=?, event_type=?, collaborators=?, priority=?, notes=?
        WHERE id=?
    """, (title, event_date, event_time, event_type, collaborators, priority, notes, event_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

# ============================
#  DELETE
# ============================
@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json(force=True)
    event_id = data.get("event_id")
    if not event_id:
        return jsonify({"status": "error"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

# ============================
#  UPLOAD FILES
# ============================
@app.route("/upload_files", methods=["POST"])
def upload_files():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    event_id = request.form.get("event_id")
    if not event_id:
        return jsonify({"status": "error"}), 400

    ensure_upload_folder()
    event_folder = os.path.join(UPLOAD_BASE, str(event_id))
    os.makedirs(event_folder, exist_ok=True)

    uploaded_paths = []
    if "files" in request.files:
        for f in request.files.getlist("files"):
            filename = f.filename
            final_path = os.path.join(event_folder, filename)
            f.save(final_path)
            rel_path = f"{event_id}/{filename}"
            uploaded_paths.append(rel_path)

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

# ============================
#  DOWNLOAD FILE
# ============================
@app.route("/download_file/<path:rel_path>")
def download_file(rel_path):
    folder, filename = os.path.split(rel_path)
    return send_from_directory(os.path.join(UPLOAD_BASE, folder), filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
