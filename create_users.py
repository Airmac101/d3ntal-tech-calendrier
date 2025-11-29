
import sqlite3

# Connexion à la base de données
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Liste des comptes à créer
users = [
    (1, "denismeuret@d3ntal-tech.fr", "D3ntalTech!@2025"),
    (2, "denismeuret01@gmail.com", "D3ntalTech!@2025"),   # staff
    (3, "isis@d3ntal-tech.com", "D3ntalTech!@2025"),     # staff
    (4, "isis.42420@gmail.com", "D3ntalTech!@2025"),     # staff
]

# Création ou mise à jour des utilisateurs
cursor.executemany("""
    INSERT OR REPLACE INTO users (id, email, password)
    VALUES (?, ?, ?)
""", users)

conn.commit()
conn.close()

print("✔ Comptes utilisateurs recréés avec succès !")
