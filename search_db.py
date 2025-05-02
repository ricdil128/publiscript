# search_db.py
import sqlite3
import os
import sys

def search_db_keywords():
    """
    Cerca nel database crisp_projects.db tutte le occorrenze di keyword nelle tabelle.
    """
    print("Script di ricerca keyword nel database crisp_projects.db")
    print("======================================================")
    
    # Verifica che il database esista
    db_path = "crisp_projects.db"
    if not os.path.exists(db_path):
        print(f"Database non trovato: {db_path}")
        return
    
    print(f"Database trovato: {db_path} ({os.path.getsize(db_path)} bytes)")
    
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Cerca tutti i progetti
    print("\n1. Progetti nel database:")
    cursor.execute("SELECT id, name, creation_date FROM projects ORDER BY creation_date DESC")
    projects = cursor.fetchall()
    
    if not projects:
        print("  Nessun progetto trovato nel database")
    else:
        for i, (proj_id, proj_name, proj_date) in enumerate(projects):
            print(f"  {i+1}. ID: {proj_id}, Nome: {proj_name}, Data: {proj_date}")
    
    # 2. Cerca variabili di tipo KEYWORD
    print("\n2. Keyword nelle variabili di progetto:")
    cursor.execute("""
        SELECT p.id, p.name, v.variable_name, v.variable_value 
        FROM projects p 
        JOIN project_variables v ON p.id = v.project_id
        WHERE v.variable_name = 'KEYWORD'
        ORDER BY p.creation_date DESC
    """)
    keywords = cursor.fetchall()
    
    if not keywords:
        print("  Nessuna variabile KEYWORD trovata")
    else:
        for i, (proj_id, proj_name, var_name, keyword) in enumerate(keywords):
            print(f"  {i+1}. ID: {proj_id}, Nome: {proj_name}, Keyword: {keyword}")
    
    # 3. Cerca possibili incoerenze
    print("\n3. Verifica incoerenze tra nome progetto e keyword:")
    potential_issues = []
    
    for proj_id, proj_name, _, keyword in keywords:
        # Verifica se il nome del progetto contiene la keyword
        if "Progetto " + keyword != proj_name and keyword not in proj_name:
            potential_issues.append((proj_id, proj_name, keyword))
    
    if not potential_issues:
        print("  ✓ Nessuna incoerenza evidente trovata")
    else:
        print("  ⚠️ Possibili incoerenze trovate:")
        for i, (proj_id, proj_name, keyword) in enumerate(potential_issues):
            print(f"  {i+1}. ID: {proj_id}, Nome: '{proj_name}', Keyword: '{keyword}'")
    
    # 4. Ricerca keyword specifiche
    if len(sys.argv) > 1:
        search_term = sys.argv[1].lower()
        print(f"\n4. Ricerca progetti con keyword contenente '{search_term}':")
        
        cursor.execute("""
            SELECT p.id, p.name, v.variable_value 
            FROM projects p 
            JOIN project_variables v ON p.id = v.project_id
            WHERE v.variable_name = 'KEYWORD' AND LOWER(v.variable_value) LIKE ?
            ORDER BY p.creation_date DESC
        """, (f"%{search_term}%",))
        
        search_results = cursor.fetchall()
        if not search_results:
            print(f"  Nessun progetto trovato con keyword contenente '{search_term}'")
        else:
            for i, (proj_id, proj_name, keyword) in enumerate(search_results):
                print(f"  {i+1}. ID: {proj_id}, Nome: {proj_name}, Keyword: {keyword}")
    
    # 5. Progetti più recenti
    print("\n5. Ultimi 3 progetti aggiunti:")
    cursor.execute("SELECT id, name, creation_date FROM projects ORDER BY creation_date DESC LIMIT 3")
    latest = cursor.fetchall()
    
    if not latest:
        print("  Nessun progetto trovato")
    else:
        for i, (proj_id, proj_name, proj_date) in enumerate(latest):
            print(f"  {i+1}. ID: {proj_id}, Nome: {proj_name}, Data: {proj_date}")
    
    # Chiudi connessione
    conn.close()
    print("\nAnalisi database completata.")

if __name__ == "__main__":
    search_db_keywords()