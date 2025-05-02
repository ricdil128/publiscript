# test_results_display_fix.py
import os
import sys
import re
from pathlib import Path

# Assicurati che la directory del progetto sia nel path
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))

try:
    # Importa correttamente dal percorso ui.book_builder
    from ui.book_builder import AIBookBuilder
    
    # Crea un mock del chat manager per i test
    class MockChatManager:
        def __init__(self):
            self.log_history = []
            self.context_file = "context.txt"  # Assicurati che questo punti al file corretto
        
        def add_log(self, message):
            print(f"LOG: {message}")
            self.log_history.append(message)
            
        def get_log_history_string(self):
            return "\n".join(self.log_history)
        
        def save_response(self, *args, **kwargs):
            print("Risposta salvata (mock)")
            
    # Crea un'istanza minima di AIBookBuilder per testare
    class TestBuilder(AIBookBuilder):
        def __init__(self):
            # Override del costruttore per evitare inizializzazioni complesse
            self.log_history = []
            self.chat_manager = MockChatManager()
            
            # Mock di results_display per verificare gli aggiornamenti
            class MockDisplay:
                def __init__(self):
                    self.value = ""
                    
                def update(self, value):
                    # Salva l'HTML generato in un file per l'ispezione
                    with open("risultati_test.html", "w", encoding="utf-8") as f:
                        f.write(value)
                    print(f"Aggiornamento risultati (salvato in risultati_test.html): {len(value)} bytes")
                    # Salva una copia per diagnosi
                    with open(f"risultati_test_debug_{len(value)}.html", "w", encoding="utf-8") as f:
                        f.write(value)
                    print(f"Copia di debug salvata in risultati_test_debug_{len(value)}.html")
                    self.value = value
            
            # Imposta i mock necessari
            self.results_display = MockDisplay()
            self.analysis_status = MockDisplay()
            
        # Override dei metodi che dipendono da altre componenti per evitare errori
        def get_current_keyword(self):
            return "test_keyword"
            
        def add_log(self, message):
            print(f"LOG: {message}")
            if not hasattr(self, 'log_history'):
                self.log_history = []
            self.log_history.append(message)
            
    # Funzione per diagnosticare il file context.txt
    def diagnose_context_file():
        print("\n=== DIAGNOSI FILE CONTEXT.TXT ===")
        try:
            # Verifica che il file esista
            if not os.path.exists("context.txt"):
                print("❌ Il file context.txt non esiste!")
                return False
                
            # Leggi contenuto
            with open("context.txt", "r", encoding="utf-8") as f:
                content = f.read()
                
            # Informazioni di base
            print(f"Dimensione file: {len(content)} bytes")
            print(f"Numero righe: {content.count(chr(10))}")
            
            # Controlla formato delle sezioni
            section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n'
            sections = re.findall(section_pattern, content)
            
            if sections:
                print(f"✅ Trovate {len(sections)} sezioni nel formato standard")
                print("Prime 5 sezioni:")
                for i, section in enumerate(sections[:5]):
                    print(f"  - {i+1}: {section}")
                    
                # Test estrazione sezioni
                print("\nTest estrazione completa...")
                section_pattern_full = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
                section_matches = re.findall(section_pattern_full, content, re.DOTALL)
                
                if section_matches:
                    print(f"✅ Estratte {len(section_matches)} sezioni complete")
                    # Verifica lunghezza contenuto sezioni
                    total_length = sum(len(content) for _, content in section_matches)
                    print(f"Lunghezza totale contenuto sezioni: {total_length} bytes")
                    
                    # Salva un esempio di sezione per debug
                    if len(section_matches) > 0:
                        title, content = section_matches[0]
                        with open("section_example.txt", "w", encoding="utf-8") as f:
                            f.write(f"=== {title} ===\n\n{content[:1000]}")
                        print("Esempio sezione salvato in section_example.txt")
                else:
                    print("❌ Estrazione completa fallita!")
            else:
                print("❌ Nessuna sezione standard trovata")
                # Cerca pattern alternativi...
                
            # Test HTML di una singola sezione per diagnosi
            try:
                print("\nCreazione HTML di test da una singola sezione...")
                # Prendi la prima sezione
                if section_matches and len(section_matches) > 0:
                    title, content = section_matches[0]
                    # Pulisci contenuto
                    content = content.replace("FINE", "").strip()
                    # Converti newline in <br> per HTML
                    content_html = content.replace("\n", "<br>")
                    
                    # Crea HTML di test
                    test_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Test Sezione</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            .section {{ padding: 15px; background-color: #f5f5f5; border-radius: 8px; }}
                            h2 {{ color: #2563eb; }}
                        </style>
                    </head>
                    <body>
                        <h1>Test di una singola sezione</h1>
                        <div class="section">
                            <h2>{title}</h2>
                            <div>{content_html}</div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Salva HTML di test
                    with open("test_section.html", "w", encoding="utf-8") as f:
                        f.write(test_html)
                    
                    print(f"✅ HTML di test creato: test_section.html ({len(test_html)} bytes)")
            except Exception as html_error:
                print(f"❌ Errore nella creazione HTML di test: {str(html_error)}")
            
            return True
                
        except Exception as e:
            print(f"❌ Errore durante la diagnosi: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    # Funzione load_analysis_results migliorata con più debug
    def load_analysis_results_debug(self):
        """Funzione per il test con più logging di debug"""
        self.add_log("Caricamento dei risultati dell'analisi...")
        
        try:
            # Verifica che il file di contesto esista
            context_file = "context.txt"
            if not os.path.exists(context_file):
                self.add_log("⚠️ File context.txt non trovato")
                if hasattr(self, 'results_display'):
                    self.results_display.update(value="<div class='alert alert-warning'>File dei risultati non trovato. Esegui prima l'analisi.</div>")
                return self.chat_manager.get_log_history_string()
            
            # Leggi il file di contesto
            with open(context_file, "r", encoding="utf-8") as f:
                context_content = f.read()
            
            self.add_log(f"Letto file context.txt: {len(context_content)} bytes")
            
            if not context_content.strip():
                self.add_log("⚠️ File context.txt vuoto")
                if hasattr(self, 'results_display'):
                    self.results_display.update(value="<div class='alert alert-warning'>File dei risultati vuoto. Esegui l'analisi.</div>")
                return self.chat_manager.get_log_history_string()
            
            # Estrai le sezioni del contesto
            sections = []
            section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
            section_matches = re.findall(section_pattern, context_content, re.DOTALL)
            
            if section_matches:
                sections = [(title.strip(), content.strip()) for title, content in section_matches]
                self.add_log(f"✅ Estratte {len(sections)} sezioni")
                
                # Debug: mostra dimensione delle prime 3 sezioni
                for i, (title, content) in enumerate(sections[:3]):
                    self.add_log(f"Sezione {i+1}: {title} ({len(content)} bytes)")
            else:
                self.add_log("⚠️ Nessuna sezione trovata con pattern standard")
                # Fallback: divide per numeri
                number_pattern = r'(\d+\).*?)(?=\d+\)|$)'
                number_matches = re.findall(number_pattern, context_content, re.DOTALL)
                
                if number_matches:
                    sections = [(f"Sezione {i+1}", content.strip()) for i, content in enumerate(number_matches)]
                    self.add_log(f"✅ Estratte {len(sections)} sezioni (pattern numerico)")
                else:
                    # Ultimo fallback: usa il testo completo
                    sections = [("Risultati completi", context_content)]
                    self.add_log("⚠️ Nessuna sezione trovata, usando il testo completo")
            
            # Costruisci l'HTML per la visualizzazione
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background-color: #2563eb; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
                    .section { background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
                    h2 { margin-top: 0; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Risultati Analisi</h1>
                    <p>File: context.txt (%d bytes)</p>
                    <p>Sezioni: %d</p>
                </div>
            """ % (len(context_content), len(sections))
            
            # Aggiungi le sezioni
            for title, content in sections:
                # Rimuovi eventuali terminatori come FINE
                content = content.replace("FINE", "").strip()
                
                # Converti newline in <br> per HTML
                content_html = content.replace("\n", "<br>")
                
                html += f"""
                <div class="section">
                    <h2>{title}</h2>
                    <div>{content_html}</div>
                </div>
                """
            
            html += """
            </body>
            </html>
            """
            
            self.add_log(f"HTML generato: {len(html)} bytes")
            
            # Salva l'HTML a parte per diagnosi
            with open("debug_html_output.html", "w", encoding="utf-8") as f:
                f.write(html)
            self.add_log("HTML salvato per diagnosi: debug_html_output.html")
            
            # Aggiorna l'interfaccia
            if hasattr(self, 'results_display'):
                self.add_log("Aggiornamento results_display...")
                self.results_display.update(value=html)
                self.add_log("✅ Risultati dell'analisi visualizzati nell'interfaccia")
            else:
                self.add_log("⚠️ results_display non disponibile")
            
            # Aggiorna lo stato dell'analisi se disponibile
            if hasattr(self, 'analysis_status'):
                self.add_log("Aggiornamento status...")
                self.analysis_status.update(value="**Stato analisi**: Completata e visualizzata ✅")
            
            return self.chat_manager.get_log_history_string()
        
        except Exception as e:
            self.add_log(f"❌ Errore nel caricamento dei risultati: {str(e)}")
            import traceback
            trace = traceback.format_exc()
            self.add_log(trace)
            
            # Salva traceback in file
            with open("error_traceback.txt", "w", encoding="utf-8") as f:
                f.write(str(e) + "\n\n" + trace)
            self.add_log("Traceback salvato in error_traceback.txt")
            
            return self.chat_manager.get_log_history_string()
            
    # Esegui il test
    def test_results_display():
        print("=== TEST VISUALIZZAZIONE RISULTATI ===")
        
        # Prima diagnostichiamo il file context.txt
        diagnose_context_file()
        
        # Verifica che context.txt esista
        if not os.path.exists("context.txt"):
            print("❌ Il file context.txt non esiste! Test impossibile.")
            return
            
        # Crea l'istanza di test
        test_builder = TestBuilder()
        
        # Assegna la funzione di test all'istanza
        import types
        test_builder.load_analysis_results = types.MethodType(load_analysis_results_debug, test_builder)
        
        # Esegui la funzione di caricamento risultati
        test_builder.load_analysis_results()
        
        # Verifica il risultato
        if os.path.exists("risultati_test.html"):
            size = os.path.getsize("risultati_test.html")
            print(f"\n✅ File HTML generato: {size} bytes")
            print("Apri 'risultati_test.html' nel browser per vedere i risultati formattati")
            
            # Verifica anche debug_html_output.html
            if os.path.exists("debug_html_output.html"):
                size_debug = os.path.getsize("debug_html_output.html")
                print(f"✅ File HTML di debug generato: {size_debug} bytes")
                print("Confronta 'debug_html_output.html' con 'risultati_test.html' per trovare differenze")
        else:
            print("❌ Nessun file HTML generato!")
            
    if __name__ == "__main__":
        test_results_display()
        
except Exception as e:
    print(f"❌ Errore nell'importazione o nell'esecuzione del test: {str(e)}")
    import traceback
    print(traceback.format_exc())