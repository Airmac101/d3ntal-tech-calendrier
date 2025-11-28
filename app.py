from flask import Flask, render_template, request, session, redirect, flash
import sqlite3
from datetime import datetime
import calendar

app = Flask(__name__)
app.secret_key = "cle_secrete_par_defaut"
DB_NAME = "calendar.db"

# ---------------- DATABASE ----------------
def get_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_db():
    conn = get_db()
    if conn:
        try:
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
            c.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    time TEXT,
                    title TEXT,
                    notes TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS appointment_users (
                    appointment_id INTEGER,
                    user_email TEXT
                )
            """)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
            conn.close()

# Initialize the database
init_db()

# ---------------- ROUTES ----------------

# Root route - redirect to /calendar
@app.route("/", methods=["GET"])
def index():
    if "user" not in session:
        return redirect("/login")  # If not logged in, redirect to login page
    return redirect("/calendar")  # If logged in, go to the calendar

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
            user = cur.fetchone()
            conn.close()

            if user:
                session["user"] = user[0]  # Store user ID in session
                return redirect("/calendar")
            else:
                flash("Invalid credentials. Please try again.", "danger")
                return render_template("login.html")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            existing_user = cur.fetchone()

            if existing_user:
                flash("Email already exists. Please login.", "warning")
                return redirect("/login")
            else:
                cur.execute("INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
                            (first_name, last_name, email, password))
                conn.commit()
                conn.close()
                flash("Registration successful! Please login.", "success")
                return redirect("/login")
    return render_template("register.html")

@app.route("/calendar", methods=["GET", "POST"])
def calendar_view():
    if "user" not in session:
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
                if conn:
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
        if conn:
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
    if conn:
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
