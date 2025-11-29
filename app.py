import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from datetime import datetime, date, timedelta
from email.mime.text import MIMEText
import smtplib
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_PATH = "database.db"

# ---------------------------------------------------------
#  INIT DATABASE
# ---------------------------------------------------------
def force_init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Table utilisateurs autorisés
    c.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
    """)

    # Table événements
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_time TEXT,
            all_day INTEGER DEFAULT 0,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            collaborators TEXT,
            notes TEXT,
            priority TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()

force_init_db()

# ---------------------------------------------------------
#  LOGIN
# ---------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM authorized_users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/calendar")
        else:
            return render_template("login.html", error="Email ou mot de passe incorrect.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------------------------------------------------
#  CALENDAR PAGE
# ---------------------------------------------------------
@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect("/")

    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    first_day = date(year, month, 1)
    start_day = first_day - timedelta(days=(first_day.weekday()))

    calendar_days = []
    current_day = start_day
    for _ in range(6):
        week = []
        for _ in range(7):
            week.append(current_day)
            current_day += timedelta(days=1)
        calendar_days.append(week)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, event_date, event_time, all_day, type, title, collaborators, notes, priority
        FROM events
        WHERE strftime('%Y-%m', event_date) = ?
    """, (f"{year}-{month:02d}",))
    rows = c.fetchall()
    conn.close()

    events_by_date = {}
    for week in calendar_days:
        for d in week:
            events_by_date[d.isoformat()] = []

    for ev in rows:
        ev_id, ev_date, ev_time, all_day, ev_type, title, collab, notes, priority = ev
        css_class = ev_type.lower().replace(" ", "")
        events_by_date[ev_date].append({
            "id": ev_id,
            "date": ev_date,
            "time": ev_time,
            "all_day": all_day,
            "type": ev_type,
            "title": title,
            "collaborators": collab,
            "notes": notes,
            "priority": priority,
            "css_class": css_class
        })

    prev_year = year if month > 1 else year - 1
    prev_month = month - 1 if month > 1 else 12
    next_year = year if month < 12 else year - 1
    next_month = month + 1 if month < 12 else 1

    month_name = first_day.strftime("%B").capitalize()

    return render_template(
        "calendar.html",
        calendar_days=calendar_days,
        events_by_date=events_by_date,
        month_name=month_name,
        year=year,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        current_day=today
    )

# ---------------------------------------------------------
#  GET EVENT BY ID
# ---------------------------------------------------------
@app.route("/event/<int:event_id>", methods=["GET"])
def get_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, event_date, event_time, all_day, type, title, collaborators, notes, priority
        FROM events WHERE id=?
    """, (event_id,))
    ev = c.fetchone()
    conn.close()

    if not ev:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": ev[0],
        "date": ev[1],
        "time": ev[2],
        "all_day": ev[3],
        "type": ev[4],
        "title": ev[5],
        "collab": ev[6],
        "notes": ev[7],
        "priority": ev[8]
    })

# ---------------------------------------------------------
#  SAVE EVENT
# ---------------------------------------------------------
@app.route("/save_event", methods=["POST"])
def save_event():
    data = request.get_json()

    ev_id = data.get("id")
    ev_date = data.get("date")
    ev_time = data.get("time")
    all_day = 1 if data.get("all_day") else 0
    ev_type = data.get("type")
    title = data.get("title")
    collab = data.get("collaborators")
    notes = data.get("notes")
    priority = data.get("priority")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if ev_id:
        c.execute("""
            UPDATE events
            SET event_date=?, event_time=?, all_day=?, type=?, title=?, collaborators=?, notes=?, priority=?
            WHERE id=?
        """, (ev_date, ev_time, all_day, ev_type, title, collab, notes, priority, ev_id))
    else:
        c.execute("""
            INSERT INTO events (event_date, event_time, all_day, type, title, collaborators, notes, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ev_date, ev_time, all_day, ev_type, title, collab, notes, priority))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ---------------------------------------------------------
#  DELETE EVENT
# ---------------------------------------------------------
@app.route("/delete_event", methods=["POST"])
def delete_event():
    data = request.get_json()
    ev_id = data.get("id")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM events WHERE id=?", (ev_id,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# ---------------------------------------------------------
#  EXPORT PDF
# ---------------------------------------------------------
@app.route("/export_pdf")
def export_pdf():
    output_path = "/var/data/export_events.pdf"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT event_date, event_time, all_day, type, title, collaborators FROM events ORDER BY event_date ASC")
    rows = c.fetchall()
    conn.close()

    pdf = canvas.Canvas(output_path)
    pdf.setFont("Helvetica", 12)

    y = 800
    pdf.drawString(30, y, "Liste des événements")
    y -= 30

    for ev in rows:
        line = f"{ev[0]} — {ev[1] if ev[1] else ''} — {ev[3]} — {ev[4]} — {ev[5]}"
        pdf.drawString(30, y, line)
        y -= 20
        if y < 40:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 800

    pdf.save()

    return send_file(output_path, as_attachment=True)

# ---------------------------------------------------------
#  RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
