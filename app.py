from flask import Flask, render_template, request, session, redirect, flash
import sqlite3
import calendar
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = "cle_secrete_par_defaut"

# ---------------- MAIL SETUP ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_email_password'  # Use app password or real password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'
mail = Mail(app)

DB_NAME = "calendar.db"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# ---------------- ROUTES ----------------

# Home route - redirect to login or register page
@app.route("/", methods=["GET"])
def index():
    if "user" not in session:  # Check if the user is logged in
        return redirect("/login")  # Redirect to the login page if not logged in
    return redirect("/calendar")  # Otherwise, redirect to the calendar page

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[4], password):  # user[4] is the password field
            session["user"] = user[0]  # Store user ID in session
            return redirect("/calendar")  # Redirect to calendar after login
        else:
            flash("Invalid credentials, please try again.")
            return render_template("login.html")
    
    return render_template("login.html")

# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                  (first_name, last_name, email, hashed_password))
        conn.commit()
        conn.close()

        # Send confirmation email
        msg = Message('Welcome to D3NTAL TECH!', recipients=[email])
        msg.body = f"Hello {first_name},\n\nYour account has been created. You can now log in with your email and password.\n\nBest regards,\nD3NTAL TECH Team"
        mail.send(msg)

        flash("Registration successful! Please check your email for confirmation.")
        return redirect("/login")
    
    return render_template("register.html")

# Calendar route
@app.route("/calendar", methods=["GET", "POST"])
def calendar_view():
    if "user" not in session:  # If user is not logged in, redirect to login
        return redirect("/login")
    
    today = datetime.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    month_name = calendar.month_name[month]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    cal = calendar.monthcalendar(year, month)
    calendar_days = []
    for week in cal:
        for day in week:
            if day != 0:
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
                conn.close()

    if request.method == "POST":
        event_date = request.form.get("event_date")
        event_time = request.form.get("event_time")
        event_title = request.form.get("event_title")
        event_notes = request.form.get("event_notes")
        collaborators = request.form.getlist("collaborators")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO appointments (date, time, title, notes) VALUES (?, ?, ?, ?)",
                    (event_date, event_time, event_title, event_notes))
        appointment_id = cur.lastrowid

        for collaborator in collaborators:
            cur.execute("INSERT INTO appointment_users (appointment_id, user_email) VALUES (?, ?)",
                        (appointment_id, collaborator))

        conn.commit()
        conn.close()

        return redirect("/calendar")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users")
    all_users = [row[0] for row in cur.fetchall()]
    conn.close()

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
        all_users=all_users
    )

if __name__ == "__main__":
    app.run(debug=True)
