from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cle_secrete_par_defaut")

DB_NAME = "calendar.db"
PASSWORD_GLOBAL = "Calendar@1010!!"  # Le mot de passe par défaut pour chaque utilisateur

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
    # Créer la table utilisateurs avec les colonnes pour le prénom, nom, email et mot de passe
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


# Initialiser la base de données si elle n'est pas encore créée
init_db()


# ---------------- EMAIL ----------------

def send_password_email(to_email):
    """Envoie un email à l'utilisateur avec son mot de passe de connexion."""
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
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        # Vérifier si l'email est déjà utilisé
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return redirect("/login?already=1")

        # Insérer l'utilisateur dans la base de données
        cur.execute("""
            INSERT INTO users (first_name, last_name, email, password)
            VALUES (?, ?, ?, ?)
        """, (first_name, last_name, email, password))
        conn.commit()
        conn.close()

        # Envoi de l'email avec le mot de passe
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
        # Vérifier si l'utilisateur existe avec l'email et le mot de passe
        cur.execute("""
            SELECT * FROM users WHERE email = ? AND password = ?
        """, (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email  # Enregistrer l'email dans la session
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()  # Supprimer l'utilisateur de la session
    return redirect("/login")


# ---------------- Fonction de test pour l'email ----------------

@app.route("/test-email")
def test_email():
    result = send_password_email(SMTP_USER)
    if result:
        return "✅ EMAIL TEST ENVOYÉ"
    else:
        return "❌ ECHEC SMTP"


if __name__ == "__main__":
    app.run(debug=True)

