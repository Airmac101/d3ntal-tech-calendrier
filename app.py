from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os
import secrets
import string

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cle_secrete_par_defaut")

DB_NAME = "calendar.db"
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

    # Créer la table des utilisateurs
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


init_db()


# ---------------- EMAIL ----------------

def send_password_email(to_email, password):
    """Envoie un email avec les informations de connexion à l'utilisateur."""
    try:
        msg = MIMEText(f"""
Bienvenue sur D3NTAL TECH ✅

Votre accès collaborateur a été créé.

Email : {to_email}
Mot de passe : {password}

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


# ---------------- SECURE PASSWORD GENERATION ----------------

def generate_secure_password(length=12):
    """Génère un mot de passe sécurisé aléatoire."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for i in range(length))


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

        # Générer un mot de passe sécurisé
        password = generate_secure_password()

        conn = get_db()
        cur = conn.cursor()

        # Vérifier si l'email existe déjà
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return redirect("/login?already=1")

        # Insérer les données de l'utilisateur et le mot de passe généré
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, password)
            VALUES (?, ?, ?, ?)
        """, (first_name, last_name, email, password))
        conn.commit()
        conn.close()

        # Envoi de l'email avec le mot de passe généré
        send_password_email(email, password)

        return redirect("/login?success=1")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM users WHERE email = ? AND password = ?
        """, (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/dashboard")
        else:
            error = "Identifiants invalides"

    return render_template("login.html", error=error)


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
