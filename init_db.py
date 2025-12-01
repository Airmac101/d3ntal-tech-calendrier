import sqlite3
import os

DB_NAME = "events.db"


def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # EVENTS
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

    # Add files column
    cur.execute("PRAGMA table_info(events);")
    columns = [c[1] for c in cur.fetchall()]
    if "files" not in columns:
        cur.execute("ALTER TABLE events ADD COLUMN files TEXT;")

    # USERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)

    # 4 ACCOUNTS WITH ORIGINAL PASSWORD
    default_users = [
        ("denismeuret01@gmail.com",       "D3ntalTech!@2025"),
        ("isis.stouvenel@d3ntal-tech.fr", "D3ntalTech!@2025"),
        ("contact@d3ntal-tech.fr",        "D3ntalTech!@2025"),
        ("admin@d3ntal-tech.fr",          "D3ntalTech!@2025")
    ]

    for email, pwd in default_users:
        cur.execute("""
            INSERT OR IGNORE INTO authorized_users (email, password)
            VALUES (?, ?)
        """, (email, pwd))

    conn.commit()
    conn.close()
    print("✔ Base initialisée avec les 4 comptes d’origine (MDP correct).")


if __name__ == "__main__":
    initialize_database()
