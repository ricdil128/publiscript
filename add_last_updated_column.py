import sqlite3
import os

def add_last_updated_column():
    # Verifica che il database esista
    db_path = "crisp_projects.db"
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se la colonna esiste già
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "last_updated" not in columns:
            # Aggiungi la colonna
            cursor.execute("ALTER TABLE projects ADD COLUMN last_updated TEXT")
            conn.commit()
            print(f"Colonna 'last_updated' aggiunta con successo alla tabella 'projects'")
            
            # Aggiorna tutti i record esistenti
            cursor.execute("UPDATE projects SET last_updated = creation_date")
            conn.commit()
            print(f"Aggiornati {cursor.rowcount} record esistenti")
        else:
            print("La colonna 'last_updated' esiste già nella tabella 'projects'")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Errore durante l'aggiunta della colonna: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_last_updated_column()
    print(f"Operazione completata: {'successo' if success else 'fallita'}")