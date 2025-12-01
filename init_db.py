import sqlite3
import json
import os

DB_NAME = "events.db"

def initialize_database():
    """
    Initialise la base de données si elle n'existe pas encore
    et ajoute la colonne 'files' si besoin.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Création de la table events si elle n'existe pas
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

    # Vérification de l'existence de la colonne 'files'
    cur.execute("PRAGMA table_info(events);")
    columns = [row[1] for row in cur.fetchall()]

    if "files" not in columns:
        print("🟦 Ajout de la colonne 'files' dans la table events...")
        cur.execute("ALTER TABLE events ADD COLUMN files TEXT;")
    else:
        print("✔ La colonne 'files' existe déjà.")

    conn.commit()
    conn.close()
    print("✔ Base de données initialisée avec succès.")


if __name__ == "__main__":
    initialize_database()
