import os
import re
import time
from datetime import datetime

def test_get_current_keyword(backup_dir="backups"):
    """Test per verificare l'estrazione corretta della keyword più recente"""
    print(f"\n{'='*50}\nTEST GET_CURRENT_KEYWORD\n{'='*50}")
    
    # Verifica se la directory backup esiste
    if not os.path.exists(backup_dir):
        print(f"⚠️ Directory {backup_dir} non trovata!")
        return "unknown"
    
    # Elenca tutti i file di backup
    backup_files = [f for f in os.listdir(backup_dir) 
                    if f.startswith("context_") and f.endswith(".txt")]
    
    if not backup_files:
        print(f"⚠️ Nessun file di backup trovato in {backup_dir}")
        return "unknown"
    
    print(f"📋 File di backup trovati: {len(backup_files)}")
    for i, file in enumerate(backup_files[:5]):  # Mostra solo primi 5
        file_path = os.path.join(backup_dir, file)
        mod_time = os.path.getmtime(file_path)
        mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f" - {i+1}: {file} (modificato: {mod_time_str})")
    
    # Ordina per data di modifica (più recente prima)
    backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
    
    if backup_files:
        latest_file = backup_files[0]
        mod_time = os.path.getmtime(os.path.join(backup_dir, latest_file))
        mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n🔍 File più recente: {latest_file} (modificato: {mod_time_str})")
        
        # Prova diversi pattern regex per estrarre la keyword
        patterns = [
            r"context_(.+?)_\d{8}_\d{6}\.txt",  # Pattern con timestamp
            r"context_(.+?)\.txt"                # Pattern senza timestamp
        ]
        
        for pattern in patterns:
            print(f"Provo pattern: {pattern}")
            keyword_match = re.match(pattern, latest_file)
            if keyword_match:
                keyword_with_underscore = keyword_match.group(1)
                keyword_with_spaces = keyword_with_underscore.replace("_", " ")
                print(f"✅ Keyword trovata: '{keyword_with_spaces}' (originale con underscore: '{keyword_with_underscore}')")
                return keyword_with_spaces
        
        print("❌ Nessun pattern ha funzionato per estrarre la keyword")
        return "unknown"
    else:
        print("❌ Nessun file di backup trovato dopo l'ordinamento (strano!)")
        return "unknown"

def test_complete_analysis_keyword_extraction():
    """Test per simulare l'estrazione della keyword nella funzione complete_analysis"""
    print(f"\n{'='*50}\nTEST SIMULAZIONE COMPLETE_ANALYSIS\n{'='*50}")
    
    try:
        # Simula i passaggi di complete_analysis per il recupero della keyword
        backup_dir = "backups"
        current_keyword = None
        
        print("1. Ricerca nei file di backup più recenti:")
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) 
                           if f.startswith("context_") and f.endswith(".txt")]
            if backup_files:
                # Ordina per data di modifica (più recente prima)
                backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), 
                               reverse=True)
                latest_file = backup_files[0]
                print(f"   🔍 File di backup più recente trovato: {latest_file}")
                
                # Estrai la keyword dal nome del file
                keyword_match = re.match(r"context_(.+?)(_\d{8}_\d{6})?\.txt", latest_file)
                if keyword_match:
                    current_keyword = keyword_match.group(1).replace("_", " ")
                    print(f"   ✅ Keyword trovata dal file più recente: {current_keyword}")
                else:
                    print("   ❌ Regex non ha trovato match nel nome del file")
            else:
                print("   ⚠️ Nessun file di backup trovato")
        else:
            print("   ⚠️ Directory backup non trovata")
        
        # Se non abbiamo trovato la keyword, fallback al metodo tradizionale
        if not current_keyword:
            print("2. Fallback al metodo tradizionale (simulato):")
            print("   ⚠️ Simulazione: get_current_keyword() restituisce 'unknown'")
            current_keyword = "unknown"
        else:
            print("2. Keyword già trovata, nessun fallback necessario")
        
        print(f"\n✅ Keyword finale: {current_keyword}")
        return current_keyword
    
    except Exception as e:
        print(f"❌ Errore nel test: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "error"

def examine_context_files():
    """Esamina tutti i file context nella directory principale"""
    print(f"\n{'='*50}\nESAME FILE CONTEXT NELLA DIRECTORY PRINCIPALE\n{'='*50}")
    
    context_files = [f for f in os.listdir() if f.startswith("context_") and f.endswith(".txt")]
    context_files += ["context.txt"] if os.path.exists("context.txt") else []
    
    if not context_files:
        print("⚠️ Nessun file context trovato nella directory principale")
        return
    
    print(f"📋 File context trovati: {len(context_files)}")
    
    for file in context_files:
        try:
            file_size = os.path.getsize(file)
            mod_time = os.path.getmtime(file)
            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"\n📄 {file} (dimensione: {file_size} bytes, modificato: {mod_time_str})")
            
            # Leggi l'inizio del file
            with open(file, "r", encoding="utf-8") as f:
                content = f.read(500)  # Leggi i primi 500 caratteri
                print(f"Anteprima inizio:")
                print("-" * 40)
                print(content.strip())
                print("-" * 40)
            
            # Cerca riferimenti a keyword nell'intero file
            with open(file, "r", encoding="utf-8") as f:
                full_content = f.read()
                # Cerca riferimenti espliciti alla keyword
                keyword_matches = re.findall(r"keyword[:\s]+([^\n,]+)", full_content, re.IGNORECASE)
                if keyword_matches:
                    print(f"Riferimenti a keyword trovati: {keyword_matches[:3]}")
        
        except Exception as e:
            print(f"❌ Errore nell'esame del file {file}: {str(e)}")

def test_file_dates():
    """Verifica le date di modifica dei file per debugging"""
    print(f"\n{'='*50}\nCONFRONTO DATE MODIFICA FILE\n{'='*50}")
    
    # Crea una lista di tutti i file nelle directory rilevanti
    files_to_check = []
    
    # File nella directory principale
    for f in os.listdir():
        if f.startswith("context_") and f.endswith(".txt"):
            files_to_check.append((f, ""))
    
    if os.path.exists("context.txt"):
        files_to_check.append(("context.txt", ""))
    
    # File nella directory backup
    backup_dir = "backups"
    if os.path.exists(backup_dir):
        for f in os.listdir(backup_dir):
            if f.startswith("context_") and f.endswith(".txt"):
                files_to_check.append((f, backup_dir))
    
    # Analizza e ordina i file per data di modifica
    file_info = []
    for filename, directory in files_to_check:
        filepath = os.path.join(directory, filename) if directory else filename
        try:
            mtime = os.path.getmtime(filepath)
            size = os.path.getsize(filepath)
            
            # Estrai keyword se possibile
            keyword = "N/A"
            match = re.match(r"context_(.+?)(_\d{8}_\d{6})?\.txt", filename)
            if match:
                keyword = match.group(1).replace("_", " ")
            
            file_info.append((filepath, mtime, size, keyword))
        except Exception as e:
            print(f"❌ Errore nell'analisi del file {filepath}: {str(e)}")
    
    # Ordina per data di modifica (più recente prima)
    file_info.sort(key=lambda x: x[1], reverse=True)
    
    # Visualizza i risultati
    print(f"📋 File trovati: {len(file_info)}")
    print(f"{'File':<40} {'Modificato':<20} {'Dimensione':<12} {'Keyword'}")
    print("-" * 80)
    
    for filepath, mtime, size, keyword in file_info:
        mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        size_str = f"{size} bytes"
        print(f"{filepath:<40} {mtime_str:<20} {size_str:<12} {keyword}")

def main():
    print(f"{'='*80}\nTEST DIAGNOSTICO KEYWORD PUBLISCRIPT\n{'='*80}")
    print(f"Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directory corrente: {os.getcwd()}")
    
    # Esegui tutti i test
    test_file_dates()
    examine_context_files()
    keyword1 = test_get_current_keyword()
    keyword2 = test_complete_analysis_keyword_extraction()
    
    print(f"\n{'='*80}\nRISULTATI FINALI\n{'='*80}")
    print(f"Keyword dal test get_current_keyword: {keyword1}")
    print(f"Keyword dal test complete_analysis: {keyword2}")
    
    # Consiglio finale
    if keyword1 == keyword2 and keyword1 != "unknown":
        print("\n✅ I test indicano che le correzioni dovrebbero funzionare correttamente.")
        print("La keyword corrente viene identificata come: " + keyword1)
    else:
        print("\n⚠️ I test mostrano differenze nei risultati o impossibilità di determinare la keyword.")
        print("Potrebbero essere necessarie ulteriori modifiche al codice.")

if __name__ == "__main__":
    main()