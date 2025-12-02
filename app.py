import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# CONFIG FLASK
# ==========================================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_key")


# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_db_connection():
    conn = sqlite3.connect("calendar.db")
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def initialize_database():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            event_date TEXT,
            event_time TEXT,
            event_type TEXT,
            collaborators TEXT,
            priority TEXT,
            notes TEXT,
            user_email TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================
# EMAIL SYSTEM
# ==========================================
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def send_event_email(subject, html_content):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = SMTP_USER

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, SMTP_USER, msg.as_string())

        print("EMAIL sent successfully.")
    except Exception as e:
        print("EMAIL ERROR:", e)


def build_event_email(subject, title, date, time, event_type, collaborators, priority, notes, user):
    return f"""
    <h2>{subject}</h2>
    <table border="1" cellpadding="6">
        <tr><td><b>Titre</b></td><td>{title}</td></tr>
        <tr><td><b>Date</b></td><td>{date}</td></tr>
        <tr><td><b>Heure</b></td><td>{time}</td></tr>
        <tr><td><b>Type</b></td><td>{event_type}</td></tr>
        <tr><td><b>Collaborateurs</b></td><td>{collaborators}</td></tr>
        <tr><td><b>Priorité</b></td><td>{priority}</td></tr>
        <tr><td><b>Notes</b></td><td>{notes}</td></tr>
        <tr><td><b>Créé / Modifié par</b></td><td>{user}</td></tr>
    </table>
    <p><i>D3NTAL TECH — Notification automatique, merci de ne pas répondre.</i></p>
    """


# ==========================================
# USER LOGIN
# ==========================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect(url_for("calendar"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ==========================================
# CALENDAR VIEW
# ==========================================
@app.route("/calendar")
def calendar():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    conn.close()

    return render_template("calendar.html", events=events, user=session["user"])


# ==========================================
# API: CREATE / UPDATE / DELETE EVENT
# ==========================================
@app.route("/api/create_event", methods=["POST"])
def api_create_event():
    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO events (title, event_date, event_time, event_type, collaborators, priority, notes, user_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["title"], data["event_date"], data["event_time"],
        data["event_type"], data["collaborators"], data["priority"],
        data["notes"], session["user"]
    ))
    conn.commit()
    conn.close()

    html = build_event_email(
        "Nouvel événement créé",
        data["title"], data["event_date"], data["event_time"],
        data["event_type"], data["collaborators"], data["priority"],
        data["notes"], session["user"]
    )
    send_event_email("D3NTAL TECH — Nouvel événement", html)

    return jsonify({"status": "ok"})


@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    data = request.form

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE events
        SET title=?, event_date=?, event_time=?, event_type=?, collaborators=?, priority=?, notes=?, user_email=?
        WHERE id=?
    """, (
        data["title"], data["event_date"], data["event_time"],
        data["event_type"], data["collaborators"], data["priority"],
        data["notes"], session["user"], data["id"]
    ))
    conn.commit()
    conn.close()

    html = build_event_email(
        "Événement modifié",
        data["title"], data["event_date"], data["event_time"],
        data["event_type"], data["collaborators"], data["priority"],
        data["notes"], session["user"]
    )
    send_event_email("D3NTAL TECH — Mise à jour d’événement", html)

    return jsonify({"status": "ok"})


@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    event_id = request.json["id"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    send_event_email("D3NTAL TECH — Suppression d’événement",
                     "<p>Un événement a été supprimé.</p>")

    return jsonify({"status": "ok"})


# ==========================================
# REMINDER SYSTEM (CRON)
# ==========================================
def check_reminders():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events")
    events = cur.fetchall()
    conn.close()

    reminders_sent = 0

    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    for ev in events:
        if ev["event_date"] == tomorrow_str:
            html = build_event_email(
                "Rappel — Événement demain",
                ev["title"], ev["event_date"], ev["event_time"],
                ev["event_type"], ev["collaborators"], ev["priority"],
                ev["notes"], ev["user_email"]
            )
            send_event_email("D3NTAL TECH — Rappel 24h", html)
            reminders_sent += 1

    return reminders_sent


@app.route("/api/check-reminders")
def api_check_reminders():
    key = request.args.get("key")

    if key != os.getenv("REMINDER_KEY", "mySuperReminderKey2025"):
        return jsonify({"error": "unauthorized"}), 401

    sent = check_reminders()
    return jsonify({"status": "ok", "reminders_sent": sent})


# ==========================================
# AUTO DB INIT AT STARTUP
# ==========================================
try:
    initialize_database()
except Exception as e:
    print("DB INIT ERROR:", e)


# ==========================================
# RUN
# ==========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
