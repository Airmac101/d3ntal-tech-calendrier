from flask import Flask, render_template, request, session, redirect
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os
import random
import string
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = "cle_secrete_par_defaut"

DB_NAME = "calendar.db"

# ---------------- DATABASE ----------------

def get_db():
    return sqlite3.connect(DB_NAME)

# Initialize the database if needed
def init_db():
    conn = get_db()
    c = conn.cursor()
    # Create users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    # Create appointments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            title TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database
init_db()


# ---------------- EMAIL ----------------

# Function to generate a random password
def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Function to send an email with the password
def send_password_email(to_email, password):
    try:
        msg = MIMEText(f"""
Bienvenue sur D3NTAL TECH ✅

Votre accès collaborateur a été créé.

Email : {to_email}
Mot de passe : {password}

Connectez-vous ici :
https://d3ntal-tech-calendrier-1.onrender.com/login
""")

        msg["Subject"] = "Accès collaborateur D3NTAL TECH"
        msg["From"] = os.environ.get("SMTP_USER")
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASSWORD"))
        server.sendmail(os.environ.get("SMTP_USER"), to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("ERREUR SMTP :", e)
        return False


# ---------------- ROUTES ----------------

# Route for home page
@app.route("/")
def home():
    return render_template("index.html")

# Route for registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")

        # Generate a password
        password = generate_password()

        # Connect to the database and insert the new user
        conn = get_db()
        cur = conn.cursor()

        # Check if the email is already registered
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return redirect("/login?already=1")

        # Insert the new user into the database
        cur.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                    (first_name, last_name, email, password))
        conn.commit()
        conn.close()

        # Send email with password to the user
        send_password_email(email, password)

        return redirect("/login?success=1")

    return render_template("register.html")


# Route for login page
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
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
        else:
            error = "Identifiants invalides"
    return render_template("login.html", error=error)


# Route for calendar view
@app.route("/calendar", methods=["GET", "POST"])
def calendar_view():
    if "user" not in session:  # Check if the user is logged in
        return redirect("/login")

    # Get the current month and year, or from the URL arguments
    today = datetime.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    month_name = calendar.month_name[month]

    # Navigate between months
    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year

    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    # Get the days of the month and check for events
    cal = calendar.monthcalendar(year, month)

    calendar_days = []
    for week in cal:
        for day in week:
            if day == 0:
                calendar_days.append({"day": None, "has_event": False})
            else:
                date_key = f"{year}-{month:02d}-{day:02d}"
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


# Route to logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
