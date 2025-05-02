# debug_console.py - Strumento di debug per PubliScript
import os
import re
import sys
import json

def menu_principale():
    """Mostra il menu principale"""
    print("\n===== PUBLISCRIPT DEBUG CONSOLE =====")
    print("1. Esaminare il file context.txt")
    print("2. Testare operazioni di esportazione")
    print("3. Verificare componenti UI")
    print("4. Esci")
    
    choice = input("\nScegli un'opzione (1-4): ")
    return choice

def esaminare_context():
    """Esamina il file context.txt"""
    context_file = "context.txt"
    
    if not os.path.exists(context_file):
        print(f"❌ File {context_file} non trovato nella directory corrente")
        print(f"Directory corrente: {os.getcwd()}")
        return
    
    # Informazioni di base
    size = os.path.getsize(context_file)
    print(f"\nFile context.txt trovato - Dimensione: {size} bytes")
    
    # Leggi contenuto
    with open(context_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Opzioni
    print("\nCosa vuoi fare?")
    print("1. Vedere le prime/ultime righe")
    print("2. Elencare tutte le sezioni")
    print("3. Cercare un testo specifico")
    print("4. Visualizzare statistiche")
    print("5. Tornare al menu principale")
    
    choice = input("\nScegli un'opzione (1-5): ")
    
    if choice == "1":
        num_lines = int(input("Quante righe vuoi vedere all'inizio/fine? "))
        lines = content.split("\n")
        print(f"\n=== PRIME {num_lines} RIGHE ===")
        for i, line in enumerate(lines[:num_lines]):
            print(f"{i+1}: {line}")
            
        print(f"\n=== ULTIME {num_lines} RIGHE ===")
        for i, line in enumerate(lines[-num_lines:]):
            print(f"{len(lines)-num_lines+i+1}: {line}")
            
    elif choice == "2":
        # Trova sezioni
        section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n'
        section_matches = re.findall(section_pattern, content)
        
        if section_matches:
            print(f"\nTrovate {len(section_matches)} sezioni:")
            for i, title in enumerate(section_matches):
                print(f"{i+1}: {title.strip()}")
                
            # Chiedi se visualizzare una sezione specifica
            sec_choice = input("\nVuoi visualizzare una sezione specifica? (numero/n): ")
            if sec_choice.lower() != "n":
                try:
                    idx = int(sec_choice) - 1
                    if 0 <= idx < len(section_matches):
                        section_title = section_matches[idx]
                        pattern = r'===\s+' + re.escape(section_title) + r'\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
                        section_content = re.search(pattern, content, re.DOTALL)
                        if section_content:
                            print(f"\n=== CONTENUTO SEZIONE: {section_title.strip()} ===\n")
                            print(section_content.group(1))
                except ValueError:
                    print("Input non valido")
        else:
            print("Nessuna sezione standard trovata")
            # Cerca pattern alternativi...
    
    elif choice == "3":
        search_text = input("\nInserisci il testo da cercare: ")
        matches = []
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if search_text.lower() in line.lower():
                matches.append((i+1, line))
        
        if matches:
            print(f"\nTrovate {len(matches)} occorrenze:")
            for line_num, line in matches[:10]:  # Limita a 10 risultati
                print(f"Linea {line_num}: {line}")
                
            if len(matches) > 10:
                print(f"... e altre {len(matches)-10} occorrenze")
        else:
            print("Nessuna occorrenza trovata")
    
    elif choice == "4":
        # Statistiche
        lines = content.split("\n")
        sections = re.findall(r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n', content)
        words = re.findall(r'\w+', content)
        
        print("\n=== STATISTICHE DEL FILE ===")
        print(f"Dimensione: {size} bytes")
        print(f"Righe: {len(lines)}")
        print(f"Parole: {len(words)}")
        print(f"Sezioni: {len(sections)}")
        print(f"Caratteri: {len(content)}")

def main():
    while True:
        choice = menu_principale()
        
        if choice == "1":
            esaminare_context()
        elif choice == "2":
            print("\nCaricamento dei test di esportazione...")
            try:
                import test_esportazione
                test_esportazione.run_all_tests()
            except ImportError:
                print("❌ File test_esportazione.py non trovato")
        elif choice == "3":
            print("\nVerifica dei componenti UI...")
            
            # Controlla se results_display è collegato correttamente
            print("Diagnostica UI:")
            print("1. Verifica se i pulsanti di esportazione sono collegati correttamente.")
            print("   - Controlla in create_interface() se export_docx_btn.click() è collegato a self.export_to_docx")
            print("   - Controlla in create_interface() se export_pdf_btn.click() è collegato a self.export_to_pdf")
            print("   - Controlla in create_interface() se export_txt_btn.click() è collegato a self.export_to_txt")
            
            print("\n2. Verifica se results_display viene aggiornato:")
            print("   - Controlla se i metodi di esportazione aggiornano self.results_display.update()")
            print("   - Controlla se analyze_market() aggiorna results_display alla fine")
            
            print("\n3. Controlla i log per errori:")
            print("   - Se vedi 'Traceback' nei log potrebbe esserci un'eccezione non gestita")
            
        elif choice == "4":
            print("\nUscita...")
            break
        else:
            print("\nScelta non valida, riprova.")

if __name__ == "__main__":
    main()