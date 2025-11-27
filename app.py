from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os
import random
import string

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cle_secrete_par_defaut")

DB_NAME = "calendar.db"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

# Fonction pour générer un mot de passe aléatoire
def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password

# Fonction pour envoyer le mot de passe par email
def send_password_email(to_email, password):
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
        print("Erreur SMTP:", e)
        return False

# Connexion à la base de données
def get_db():
    return sqlite3.connect(DB_NAME)

# Initialisation de la base de données
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom TEXT,
            nom TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        prenom = request.form.get("prenom")
        nom = request.form.get("nom")
        email = request.form.get("email")
        
        # Vérification si l'utilisateur existe déjà
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return redirect("/login?already=1")

        # Générer un mot de passe aléatoire
        password = generate_password()

        # Sauvegarder l'utilisateur dans la base de données
        cur.execute("INSERT INTO users (prenom, nom, email, password) VALUES (?, ?, ?, ?)",
                    (prenom, nom, email, password))
        conn.commit()
        conn.close()

        # Envoyer le mot de passe par email
        send_password_email(email, password)

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
            return redirect("/dashboard")

    return render_template("login.html")

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
