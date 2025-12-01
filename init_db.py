import sqlite3
import os

DB_NAME = "events.db"


def initialize_database():
    """
    Initialise la base de données :
    - Crée la table events
    - Ajoute la colonne files si absente
    - Crée la table authorized_users
    - Ajoute les 4 comptes d'origine
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ==============================
    # TABLE EVENTS
    # ==============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            event_time TEXT NOT NULL,
            event_type TEXT NOT NULL,
            collaborators TEXT,
            priority TEXT,
            notes TEXT,
            user_email TEXT
        );
    """)

    # Vérifier si la colonne 'files' existe
    cur.execute("PRAGMA table_info(events);")
    columns = [row[1] for row in cur.fetchall()]

    if "files" not in columns:
        print("🟦 Ajout de la colonne 'files' dans events...")
        cur.execute("ALTER TABLE events ADD COLUMN files TEXT;")
    else:
        print("✔ Colonne 'files' déjà présente")


    # ==============================
    # TABLE AUTHORIZED_USERS
    # ==============================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    print("✔ Table authorized_users vérifiée")

    # ==============================
    # AJOUT DES 4 COMPTES ORIGINAUX
    # ==============================
    default_password = "D3ntalTech!@2025"

    default_users = [
        ("denismeuret01@gmail.com",       default_password),
        ("isis.stouvenel@d3ntal-tech.fr", default_password),
        ("denismeuret@d3ntal-tech.fr",        default_password),
        ("isis.42420@gmail.com",          default_password)
    ]

    for email, pwd in default_users:
        cur.execute("""
            INSERT OR IGNORE INTO authorized_users (email, password)
            VALUES (?, ?)
        """, (email, pwd))

    print("✔ Comptes utilisateurs ajoutés (MDP original, sans doublons)")

    conn.commit()
    conn.close()
    print("✔ Base de données initialisée avec succès.")


if __name__ == "__main__":
    initialize_database()
