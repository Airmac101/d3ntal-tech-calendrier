from flask import Flask, render_template, request, session, redirect, flash
from datetime import datetime
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

# Hardcoded authorized email addresses
AUTHORIZED_EMAILS = [
    'denismeuret01@gmail.com',
    'denismeuret@d3ntal-tech.fr',
    'isis.stouvenel@d3ntal-tech.fr'
]

DB_NAME = "calendar.db"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect(DB_NAME)

# Initialize the database (assuming it's already initialized)
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

# ---------------- ROUTES ----------------

# Home route - redirect to login or register page
@app.route("/", methods=["GET"])
def index():
    if "user" not in session:
        return redirect("/login")  # Redirect to login if user is not logged in
    return redirect("/calendar")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        # Check if email is in the authorized list
        if email not in AUTHORIZED_EMAILS:
            flash("Your email is not authorized to access this application.")
            return render_template("login.html")

        # For simplicity, we can skip password validation for this version, since we're only checking the email
        session["user"] = email  # Store user email in session
        return redirect("/login_successful")
    
    return render_template("login.html")

# Login success route
@app.route("/login_successful", methods=["GET"])
def login_successful():
    return render_template("login_successful.html")

# Calendar route
@app.route("/calendar", methods=["GET", "POST"])
def calendar_view():
    if "user" not in session:
        return redirect("/login")  # If user is not logged in, redirect to login

    today = datetime.today()
    year = int(request.args.get("year", today.year))
    month = int(request.args.get("month", today.month))

    # Calendar logic here...

    return render_template("calendar.html")

if __name__ == "__main__":
    app.run(debug=True)
