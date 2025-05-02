import re
import os
import time

def test_context_extraction():
    """
    Test per verificare se complete_analysis() sta cercando in tutto il file
    invece di cercare solo nelle sezioni della keyword corrente
    """
    print("=== TEST ESTRAZIONE DATI DA CONTEXT.TXT ===\n")
    
    # 1. Verifica se il file context.txt esiste
    context_file = "context.txt"
    if not os.path.exists(context_file):
        print(f"File {context_file} non trovato!")
        return False
    
    # 2. Leggi il contenuto del file
    with open(context_file, "r", encoding="utf-8") as f:
        context_content = f.read()
    
    print(f"Dimensione del file context.txt: {len(context_content)} caratteri")
    
    # 3. Analizza il problema: cerca ovunque vs cerca in sezioni specifiche
    
    # 3.1 Il metodo attuale che cerca in tutto il file
    print("\n--- RICERCA IN TUTTO IL FILE ---")
    title_pattern = r'7\)[^:]*:[^T]*Titolo[^:]*:[^\n]*\n([^\n]+)'
    title_match = re.search(title_pattern, context_content, re.IGNORECASE)
    
    if title_match:
        print("✓ Titolo trovato con ricerca globale:")
        print(f"   '{title_match.group(1).strip()}'")
    else:
        print("✗ Nessun titolo trovato con ricerca globale")
    
    # 3.2 Verifica le keyword presenti nel file
    print("\n--- KEYWORD PRESENTI NEL FILE ---")
    
    # Cerca tutte le sezioni "Analisi Legacy"
    section_pattern = r'=== Analisi Legacy[^=]*?-\s+([^-\s]+)[^=]*?===\s+'
    keyword_matches = re.finditer(section_pattern, context_content)
    
    keywords = set()
    for match in keyword_matches:
        keyword = match.group(1)
        keywords.add(keyword)
    
    print(f"Trovate {len(keywords)} keyword uniche: {', '.join(keywords)}")
    
    # 3.3 Test con una keyword specifica - simula ciò che dovrebbe fare complete_analysis()
    print("\n--- RICERCA PER KEYWORD SPECIFICA ---")
    
    # Keyword che vuoi testare
    test_keyword = "Fortran_for_Beginners"
    
    # Cerca sezioni specifiche per questa keyword
    keyword_pattern = re.compile(f"=== Analisi Legacy[^=]*{test_keyword}[^=]*===", re.IGNORECASE)
    matches = list(keyword_pattern.finditer(context_content))
    
    if matches:
        print(f"✓ Trovate {len(matches)} sezioni per {test_keyword}")
        
        # Estrai la sezione più recente
        sections_with_timestamp = []
        for match in matches:
            section_text = match.group(0)
            timestamp_match = re.search(r'(\d{8}_\d{6})', section_text)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                sections_with_timestamp.append((section_text, timestamp))
        
        if sections_with_timestamp:
            # Ordina per timestamp (più recente prima)
            sections_with_timestamp.sort(key=lambda x: x[1], reverse=True)
            most_recent = sections_with_timestamp[0]
            most_recent_section = most_recent[0]
            timestamp = most_recent[1]
            
            print(f"✓ Sezione più recente: {timestamp}")
            
            # Trova i limiti della sezione
            start_idx = context_content.find(most_recent_section)
            end_idx = context_content.find("===", start_idx + len(most_recent_section))
            
            if start_idx > 0 and end_idx > start_idx:
                # Estrai solo il contenuto della sezione corrente
                section_content = context_content[start_idx:end_idx]
                
                print(f"✓ Contenuto sezione estratto: {len(section_content)} caratteri")
                
                # Cerca titolo SOLO in questa sezione
                section_title_match = re.search(r'Titolo[^:]*:[^\n]*\n([^\n]+)', section_content, re.IGNORECASE)
                
                if section_title_match:
                    print(f"✓ Titolo trovato nella sezione specifica:")
                    print(f"   '{section_title_match.group(1).strip()}'")
                else:
                    # Cerca proposte o altre informazioni
                    proposal_match = re.search(r'Proposta \d+:\s+[""]?([^"\n]+)[""]?', section_content)
                    
                    if proposal_match:
                        print(f"✓ Proposta trovata nella sezione specifica:")
                        print(f"   '{proposal_match.group(1).strip()}'")
                    else:
                        print("✗ Nessun titolo o proposta trovato nella sezione specifica")
    else:
        print(f"✗ Nessuna sezione trovata per {test_keyword}")
    
    print("\n=== CONCLUSIONE ===")
    print("Se il titolo trovato con la ricerca globale è diverso da quello trovato nella sezione specifica,")
    print("allora il problema è che complete_analysis() sta cercando in tutto il file invece di cercare")
    print("solo nelle sezioni relative alla keyword corrente.")
    
    return True

if __name__ == "__main__":
    test_context_extraction()