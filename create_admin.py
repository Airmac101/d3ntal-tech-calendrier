import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Création / mise à jour du compte administrateur
cursor.execute("""
INSERT OR REPLACE INTO users (id, email, password)
VALUES (1, 'denismeuret01@gmail.com', 'D3ntalTech!@2025');
""")

conn.commit()
conn.close()

print("✔ Compte administrateur recréé avec succès.")

