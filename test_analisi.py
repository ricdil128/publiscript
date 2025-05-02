import os
import re
import json
import shutil
from datetime import datetime

def log(message):
    """Funzione semplificata di logging"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_estrazione_keyword():
    """Test per la funzione di estrazione della keyword"""
    log("TEST: Estrazione keyword")
    
    # Controlla i file di backup nella directory backups/
    backup_dir = "backups"
    keyword = None
    
    if os.path.exists(backup_dir):
        log(f"Directory backup trovata: {backup_dir}")
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("context_") and f.endswith(".txt")]
        
        if backup_files:
            # Ordina per data di modifica (più recente prima)
            backup_files = sorted(backup_files, 
                                 key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), 
                                 reverse=True)
            
            # Stampa i primi 5 file di backup più recenti
            log(f"File di backup più recenti:")
            for i, file in enumerate(backup_files[:5]):
                modified_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, file)))
                log(f"  {i+1}. {file} (modificato: {modified_time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # Estrai la keyword dal primo file (il più recente)
            latest_file = backup_files[0]
            log(f"Analisi file più recente: {latest_file}")
            
            # Estrazione con diversi pattern
            patterns = [
                r"context_(.+?)_\d{8}_\d{6}\.txt",  # Pattern con timestamp
                r"context_(.+?)\.txt"                # Pattern senza timestamp
            ]
            
            for pattern in patterns:
                match = re.match(pattern, latest_file)
                if match:
                    raw_keyword = match.group(1)
                    keyword = raw_keyword.replace("_", " ")
                    log(f"✅ Keyword estratta con pattern '{pattern}': '{keyword}' (raw: '{raw_keyword}')")
                    break
    
    # Cerca anche nel file context.txt principale
    if os.path.exists("context.txt"):
        log("Analisi del file context.txt")
        try:
            with open("context.txt", "r", encoding="utf-8") as f:
                content = f.read(2000)  # Leggi solo i primi 2000 caratteri
                
                # Cerca menzioni di keyword
                keyword_patterns = [
                    r"keyword:\s*([^\n]+)",
                    r"KEYWORD:\s*([^\n]+)",
                    r"Chess for (.+?)\b"
                ]
                
                for pattern in keyword_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        context_keyword = match.group(1).strip()
                        log(f"✅ Keyword trovata nel context.txt con pattern '{pattern}': '{context_keyword}'")
                        if not keyword:
                            keyword = context_keyword
        except Exception as e:
            log(f"❌ Errore nella lettura di context.txt: {str(e)}")
    
    # Risultato finale
    if keyword:
        log(f"✅ RISULTATO: Keyword estratta = '{keyword}'")
    else:
        log("❌ RISULTATO: Impossibile estrarre la keyword")
        
    return keyword

def test_generazione_html(keyword):
    """Test per la funzione di generazione HTML"""
    log("\nTEST: Generazione HTML")
    
    if not keyword:
        log("❌ Keyword non disponibile, impossibile generare HTML")
        return False
    
    # Directory di output
    output_dir = "output/analisi_html"
    os.makedirs(output_dir, exist_ok=True)
    
    # Sanitizza la keyword per il nome file
    safe_keyword = re.sub(r'[\\/*?:"<>|]', "", keyword).replace(" ", "_")[:30]
    log(f"Keyword sanitizzata per nome file: '{safe_keyword}'")
    
    # Cerca file HTML esistenti per questa keyword
    html_files = []
    if os.path.exists(output_dir):
        html_files = [f for f in os.listdir(output_dir) if safe_keyword in f and f.endswith(".html")]
    
    if html_files:
        log(f"🔍 Trovati {len(html_files)} file HTML per la keyword '{keyword}':")
        for i, file in enumerate(html_files):
            file_path = os.path.join(output_dir, file)
            file_size = os.path.getsize(file_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            log(f"  {i+1}. {file} ({file_size} bytes, modificato: {modified_time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # Analizza il contenuto HTML
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    
                # Verifica se è un HTML valido
                if html_content.strip().startswith("<!DOCTYPE") or html_content.strip().startswith("<html"):
                    log(f"  ✅ File contiene HTML valido")
                    
                    # Conta le sezioni principali nell'HTML
                    section_count = html_content.count('<div class="section">')
                    log(f"  📊 Numero di sezioni trovate: {section_count}")
                    
                    # Cerca contenuti duplicati
                    title_pattern = r"<title[^>]*>([^<]+)</title>"
                    titles = re.findall(title_pattern, html_content)
                    if len(titles) > 1:
                        log(f"  ⚠️ PROBLEMA: Trovati {len(titles)} tag title - possibile duplicazione")
                    
                    # Verifica la presenza del contenuto
                    if html_content.count("Buyer") > 1 or html_content.count("Persona") > 1:
                        log(f"  ⚠️ PROBLEMA: Possibile contenuto duplicato (Buyer Persona appare più volte)")
                    
                    # Verifica se ci sono principalmente stili senza contenuto
                    css_size = len(re.findall(r"<style[^>]*>.*?</style>", html_content, re.DOTALL))
                    if css_size > 0 and section_count < 2:
                        log(f"  ⚠️ PROBLEMA: Il file contiene {css_size} blocchi CSS ma poche sezioni di contenuto")
            except Exception as e:
                log(f"  ❌ Errore nell'analisi del file HTML: {str(e)}")
    else:
        log(f"❌ Nessun file HTML trovato per la keyword '{keyword}'")
    
    # Test: genera un nuovo HTML di test
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_html_path = os.path.join(output_dir, f"test_{safe_keyword}_{timestamp}.html")
        
        # HTML minimo per il test
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Analisi Test: {keyword}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .section {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; }}
        h1 {{ color: #3f51b5; }}
    </style>
</head>
<body>
    <h1>Analisi di Mercato: {keyword}</h1>
    <p>Test generato il {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    
    <div class="section">
        <h2>Buyer Persona</h2>
        <p>Profilo demografico e psicografico essenziale per {keyword}</p>
    </div>
    
    <div class="section">
        <h2>Analisi Keyword</h2>
        <p>Dati di mercato per la keyword "{keyword}"</p>
    </div>
</body>
</html>"""
        
        # Salva il file HTML di test
        with open(test_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        log(f"✅ File HTML di test creato: {test_html_path} ({os.path.getsize(test_html_path)} bytes)")
        
        # Test keyword nel file corrente
        context_file = f"context_{safe_keyword}.txt"
        if os.path.exists(context_file):
            log(f"✅ File context trovato: {context_file} ({os.path.getsize(context_file)} bytes)")
        else:
            log(f"❌ File context non trovato: {context_file}")
            
            # Cerca nei formati alternativi
            for ext in [".txt", "_current.txt"]:
                alt_file = f"context_{safe_keyword}{ext}"
                if os.path.exists(alt_file):
                    log(f"✅ File context alternativo trovato: {alt_file} ({os.path.getsize(alt_file)} bytes)")
            
            # Controlla se c'è un file context.txt generico
            if os.path.exists("context.txt"):
                log(f"✅ File context generico trovato: context.txt ({os.path.getsize('context.txt')} bytes)")
        
        return True
    except Exception as e:
        log(f"❌ Errore nella generazione del file HTML di test: {str(e)}")
        return False

def test_database_analisi():
    """Test per il database delle analisi"""
    log("\nTEST: Database analisi")
    
    db_path = "crisp_projects.db"
    if not os.path.exists(db_path):
        log(f"❌ Database non trovato: {db_path}")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Controlla le tabelle
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [t[0] for t in tables]
        log(f"📋 Tabelle trovate nel database: {', '.join(table_names)}")
        
        # Estrai progetti
        if 'projects' in table_names:
            cursor.execute("SELECT id, name, creation_date FROM projects ORDER BY creation_date DESC LIMIT 5;")
            projects = cursor.fetchall()
            
            log(f"📊 Ultimi {len(projects)} progetti nel database:")
            for project in projects:
                proj_id, name, date = project
                log(f"  • ID: {proj_id}, Nome: {name}, Data: {date}")
                
                # Estrai variabili del progetto
                cursor.execute("SELECT variable_name, variable_value FROM project_variables WHERE project_id = ? AND variable_name = 'KEYWORD' LIMIT 1;", (proj_id,))
                keyword_var = cursor.fetchone()
                
                if keyword_var:
                    var_name, var_value = keyword_var
                    log(f"    ✓ Keyword: {var_value}")
                else:
                    log(f"    ✗ Keyword non trovata")
        
        conn.close()
        return True
    except Exception as e:
        log(f"❌ Errore nell'analisi del database: {str(e)}")
        return False

def esegui_test_completo():
    """Esegui tutti i test"""
    log("=== INIZIO TEST DIAGNOSTICI ===")
    log(f"Directory corrente: {os.getcwd()}")
    log(f"Ora corrente: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Estrazione keyword
    keyword = test_estrazione_keyword()
    
    # Test 2: Generazione HTML
    test_generazione_html(keyword)
    
    # Test 3: Database
    test_database_analisi()
    
    log("=== FINE TEST DIAGNOSTICI ===")

if __name__ == "__main__":
    esegui_test_completo()