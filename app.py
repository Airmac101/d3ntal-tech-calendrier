from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os
import calendar
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cle_secrete_par_defaut")

DB_NAME = "calendar.db"
PASSWORD_GLOBAL = "Calendar@1010!!"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


# ---------------- DATABASE ----------------

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            first_name TEXT,
            last_name TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            title TEXT,
            notes TEXT,
            user_email TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------- EMAIL ----------------

def send_password_email(to_email):
    try:
        msg = MIMEText(f"""
Bienvenue sur D3NTAL TECH ✅

Votre accès collaborateur a été créé.

Email : {to_email}
Mot de passe : {PASSWORD_GLOBAL}

Connectez-vous ici :
https://d3ntal-tech-calendrier.onrender.com/login
""")

        msg["Subject"] = "Accès collaborateur D3NTAL TECH"
        msg["From"] = SMTP_USER
        msg["To"] = to_email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("ERREUR SMTP :", e)
        return False


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return redirect("/login?already=1")

        cur.execute("INSERT INTO users (email, password, first_name, last_name) VALUES (?, ?, ?, ?)",
                    (email, PASSWORD_GLOBAL, first_name, last_name))
        conn.commit()
        conn.close()

        send_password_email(email)

        return redirect("/login?success=1")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/calendar")

    return render_template("login.html")


@app.route("/calendar", methods=["GET", "POST"])
def calendar_view():
    if "user" not in session:
        return redirect("/login")

    # Obtenez l'année et le mois actuels à partir des paramètres de l'URL
    today = datetime.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    # Utiliser le module calendar pour générer le mois
    month_name = calendar.month_name[month]
    
    # Navigation du mois
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year

    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    # Récupérer les jours du mois
    cal = calendar.monthcalendar(year, month)

    # Convertir chaque jour en un format pour l'affichage
    calendar_days = []
    for week in cal:
        for day in week:
            if day == 0:
                calendar_days.append({"day": None, "has_event": False})
            else:
                date_key = f"{year}-{month:02d}-{day:02d}"
                # Vérifiez les événements associés à cette date
                conn = get_db()
                cur = conn.cursor()
                cur.execute("SELECT * FROM appointments WHERE date = ?", (date_key,))
                events = cur.fetchall()
                has_event = len(events) > 0
                calendar_days.append({
                    "day": day,
                    "has_event": has_event
                })

    return render_template(
        "calendar.html",
        year=year,
        month=month,
        month_name=month_name,
        calendar_days=calendar_days,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
