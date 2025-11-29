import sqlite3
import os

# Dossier DB
DB_DIR = "db"
DB_PATH = os.path.join(DB_DIR, "database.db")

# Création du dossier si absent
os.makedirs(DB_DIR, exist_ok=True)

# Connexion
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---------------------------------------------------------
# TABLE 1 — Utilisateurs autorisés
# ---------------------------------------------------------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

# ---------------------------------------------------------
# TABLE 2 — Événements du calendrier
# ---------------------------------------------------------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        event_date TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

# ---------------------------------------------------------
# TABLE 3 — Logs de connexion
# ---------------------------------------------------------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        ip TEXT,
        login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
""")

conn.commit()
conn.close()

print("✅ Base SQLite créée avec succès !")
print(f"📁 Emplacement : {DB_PATH}")
