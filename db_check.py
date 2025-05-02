# Salva questo file come db_check.py
import sqlite3
import os

def check_database_structure():
    # Trova il database nella directory corrente
    db_path = "crisp_projects.db"
    if not os.path.exists(db_path):
        print(f"ERRORE: Database non trovato in: {os.getcwd()}")
        return
    
    print(f"Database trovato: {db_path}")
    print(f"Directory corrente: {os.getcwd()}")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lista tutte le tabelle
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\nTabelle nel database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Per ogni tabella, mostra la struttura
    for table in tables:
        table_name = table[0]
        print(f"\nStruttura della tabella '{table_name}':")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            print(f"  {col_name} ({col_type}){' [PK]' if pk else ''}{' [NOT NULL]' if not_null else ''}")
    
    # Mostra alcune righe di esempio per project_variables
    try:
        print("\nEsempio di righe nella tabella project_variables:")
        cursor.execute("SELECT * FROM project_variables LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  Nessuna riga trovata")
    except Exception as e:
        print(f"Errore nella lettura di project_variables: {str(e)}")
    
    # Chiudi connessione
    conn.close()
    print("\nAnalisi database completata.")

if __name__ == "__main__":
    check_database_structure()