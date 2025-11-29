import sqlite3
import os
import hashlib

DB_DIR = "db"
DB_PATH = os.path.join(DB_DIR, "database.db")

# Sel pour le hash (doit être identique à celui utilisé dans app.py)
SALT = "D3NTAL_TECH_SUPER_SALT_2025"


def hash_password(plain_password: str) -> str:
    """
    Retourne un hash sécurisé du mot de passe.
    """
    to_hash = (SALT + plain_password).encode("utf-8")
    return hashlib.sha256(to_hash).hexdigest()


def init_db():
    """
    Crée la base SQLite et la table authorized_users,
    puis insère les utilisateurs autorisés avec le mot de passe hashé.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table des utilisateurs autorisés
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS authorized_users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Mot de passe unique pour tous (hashé)
    plain_password = "D3ntalTech!@2025"
    pwd_hash = hash_password(plain_password)

    # Liste des emails autorisés
    authorized_emails = [
        "denismeuret01@gmail.com",
        "isis.stouvenel@d3ntal-tech.fr",
        "isis.42420@gmail.com",
        "denismeuret@d3ntal-tech.fr",
    ]

    # Insertion / mise à jour
    for email in authorized_emails:
        cursor.execute(
            """
            INSERT OR REPLACE INTO authorized_users (email, password_hash)
            VALUES (?, ?);
            """,
            (email, pwd_hash),
        )

    conn.commit()
    conn.close()

    print("✅ Base de données initialisée avec succès.")
    print(f"📁 Emplacement : {DB_PATH}")


if __name__ == "__main__":
    init_db()
