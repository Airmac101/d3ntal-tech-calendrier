from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    jsonify,
    send_file,
)
import sqlite3
import os
import calendar
from datetime import datetime, date
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------------------------------
# CONFIG FLASK
# ------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "SUPER_SECRET_KEY_D3NTAL_TECH_2025")

# Base SQLite sur disque persistant Render
DB_PATH = "/var/data/database.db"
SALT = "D3NTAL_TECH_SUPER_SALT_2025"


# ------------------------------------------------
# EMAIL — UTILITAIRE GLOBAL
# ------------------------------------------------
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
        print("EMAIL WARNING: SMTP configuration incomplete.")
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
        print("EMAIL SENT")
    except Exception as e:
        print("EMAIL ERROR:", e)


def build_event_email(
    action,
    title,
    event_date,
    event_time,
    event_type,
    collaborators,
    priority,
    notes,
    user_email,
):
    html = f"""
    <div style="font-family: Arial; padding:20px;">
      <h2 style="color:#2F80ED;">{action} — D3NTAL TECH</h2>
      <table style="border-collapse:collapse;width:100%;">
        <tr><td><b>Titre</b></td><td>{title}</td></tr>
        <tr><td><b>Date</b></td><td>{event_date}</td></tr>
        <tr><td><b>Heure</b></td><td>{event_time}</td></tr>
        <tr><td><b>Type</b></td><td>{event_type}</td></tr>
        <tr><td><b>Collaborateurs</b></td><td>{collaborators}</td></tr>
        <tr><td><b>Priorité</b></td><td>{priority}</td></tr>
        <tr><td><b>Notes</b></td><td>{notes}</td></tr>
        <tr><td><b>Modifié par</b></td><td>{user_email}</td></tr>
      </table>
    </div>
    """
    return html


# ------------------------------------------------
# DB UTILS
# ------------------------------------------------
def hash_password(pwd: str):
    return hashlib.sha256((SALT + pwd).encode()).hexdigest()


def get_db_connection():
    os.makedirs("/var/data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def force_init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Table utilisateurs
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS authorized_users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Alimentation des comptes autorisés (3e colonne auto-remplie)
    pwd = hash_password("D3ntalTech!@2025")
    for email in [
        "denismeuret01@gmail.com",
        "isis.stouvenel@d3ntal-tech.fr",
        "isis.42420@gmail.com",
        "denismeuret@d3ntal-tech.fr",
    ]:
        cur.execute(
            """
            INSERT OR REPLACE INTO authorized_users (email, password_hash)
            VALUES (?, ?)
            """,
            (email, pwd),
        )

    # Table événements
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

    conn.commit()
    conn.close()


# ------------------------------------------------
# AUTH
# ------------------------------------------------
def check_credentials(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM authorized_users WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    return row and row["password_hash"] == hash_password(password)


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if check_credentials(email, password):
            session["user"] = email
            return redirect("/calendar")
        error = "Email ou mot de passe incorrect."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------------------------------------
# CALENDRIER
# ------------------------------------------------
def event_type_to_css(t):
    t = (t or "").lower()
    if "fourn" in t or "rendez" in t:
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


@app.route("/calendar")
def calendar_page():
    if "user" not in session:
        return redirect("/")

    now = datetime.now()
    today = date.today()

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

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)
    month_name = calendar.month_name[month]

    conn = get_db_connection()
    cur = conn.cursor()

    # Événements du mois affiché
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
    conn.close()

    # Événements par date pour les cases du calendrier
    events_by_date = {}
    for r in rows:
        key = r["event_date"]
        events_by_date.setdefault(key, []).append(
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

    # Récapitulatif simple classé par jour
    month_summary = {}
    for r in rows:
        d_iso = r["event_date"]
        if d_iso not in month_summary:
            month_summary[d_iso] = {
                "date": date.fromisoformat(d_iso),
                "events": [],
            }
        month_summary[d_iso]["events"].append(
            {
                "time": r["event_time"],
                "type": r["event_type"],
                "title": r["title"],
                "collab": r["collaborators"] or "",
                "priority": r["priority"],
                "notes": r["notes"],
            }
        )

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
        week_summary=month_summary,  # utilisé par ton récapitulatif
        week_start=month_start,
        week_end=month_end,
    )


# ------------------------------------------------
# API EVENTS
# ------------------------------------------------
@app.route("/api/add_event", methods=["POST"])
def api_add_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json()
    title = data["title"]
    event_date = data["event_date"]
    event_time = data["event_time"]
    event_type = data["event_type"]
    collaborators = data.get("collaborators", "")
    priority = data.get("priority", "Normal")
    notes = data.get("notes", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events 
        (user_email,title,event_date,event_time,event_type,collaborators,priority,notes)
        VALUES (?,?,?,?,?,?,?,?)
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

    return jsonify({"status": "success"})


@app.route("/api/update_event", methods=["POST"])
def api_update_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json()
    event_id = data["event_id"]

    title = data["title"]
    event_date = data["event_date"]
    event_time = data["event_time"]
    event_type = data["event_type"]
    collaborators = data.get("collaborators", "")
    priority = data.get("priority", "Normal")
    notes = data.get("notes", "")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE events
        SET title=?,event_date=?,event_time=?,event_type=?,
            collaborators=?,priority=?,notes=?
        WHERE id=? AND user_email=?
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
            session["user"],
        ),
    )
    conn.commit()
    conn.close()

    html = build_event_email(
        "Événement modifié",
        title,
        event_date,
        event_time,
        event_type,
        collaborators,
        priority,
        notes,
        session["user"],
    )
    send_event_email("D3NTAL TECH — Événement modifié", html)

    return jsonify({"status": "success"})


@app.route("/api/delete_event", methods=["POST"])
def api_delete_event():
    if "user" not in session:
        return jsonify({"status": "error"}), 403

    data = request.get_json()
    event_id = data["event_id"]

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM events WHERE id=? AND user_email=?",
        (event_id, session["user"]),
    )
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

    cur.execute(
        "DELETE FROM events WHERE id=? AND user_email=?",
        (event_id, session["user"]),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "success"}


# ------------------------------------------------
# EXPORT PDF PRO
# ------------------------------------------------
@app.route("/export_pdf")
def export_pdf():
    if "user" not in session:
        return redirect("/")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY event_date,event_time;")
    rows = cur.fetchall()
    conn.close()

    out_path = "/var/data/export_events.pdf"
    doc = SimpleDocTemplate(out_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Logo + bandeau
    logo_path = "static/logo.png"
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=140, height=40))
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "<b><font size=16 color='#2F80ED'>Récapitulatif des événements — D3NTAL TECH</font></b>",
            styles["Title"],
        )
    )
    story.append(Spacer(1, 20))

    data = [["Date", "Heure", "Titre", "Type", "Collaborateurs", "Priorité", "Notes"]]
    for r in rows:
        data.append(
            [
                r["event_date"],
                r["event_time"],
                r["title"],
                r["event_type"],
                r["collaborators"] or "",
                r["priority"],
                r["notes"],
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F80ED")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.gray),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
            ]
        )
    )

    story.append(table)
    doc.build(story)

    return send_file(
        out_path,
        as_attachment=True,
        download_name="evenements_d3ntaltech.pdf",
    )


# ------------------------------------------------
# MAIN
# ------------------------------------------------
if __name__ == "__main__":
    force_init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

force_init_db()
