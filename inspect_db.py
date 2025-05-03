import sqlite3

db_path = r"C:\Users\a\Documents\PubliScript_Refactored\crisp_projects.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, creation_date FROM projects ORDER BY creation_date DESC")
    rows = cursor.fetchall()

    print("\n📋 Progetti nel database:\n")
    for row in rows:
        print(f"- ID: {row[0]}, Nome: {row[1]}, Data: {row[2]}")

    conn.close()
except Exception as e:
    print(f"❌ Errore durante l'accesso al database: {e}")
