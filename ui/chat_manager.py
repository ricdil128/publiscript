"""
Gestione chat e file di contesto.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

class ChatManager:
    def __init__(self, parent=None):
        self.context_file = "context.txt"
        self.backup_dir = Path("backups")
        self.upload_selector = "div.upload-attachments.flex.items-center"
        self.backup_dir.mkdir(exist_ok=True)
        self.parent = parent
        self.log_history = []

    def log_prompt_location(self, prompt_id, section_number, action, details=None):
        """Helper per tracciare la posizione nel flusso CRISP"""
        location = f"Prompt {section_number} di {prompt_id}"
        message = f"[{location}] {action}"
        if details:
            message += f": {details}"
        self.add_log(message)
        return location
    
    def add_log(self, message):
        """Aggiunge un messaggio al log e restituisce il log aggiornato"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Includi millisecondi
        formatted_message = f"[{timestamp}] {message}"
    
        # Aggiunge al log di sistema
        logging.info(message)
    
        # Limita la dimensione della cronologia dei log per evitare rallentamenti
        if len(self.log_history) > 500:  # Mantieni solo gli ultimi 500 messaggi
            self.log_history = self.log_history[-499:]
    
        self.log_history.append(formatted_message)
    
        # Restituisci il log aggiornato
        return "\n".join(self.log_history)
        
    def save_response(self, response, section, metadata=None):
        """Salva la risposta con metadati, sovrascrivendo il file di contesto principale"""
        print(f"DEBUG: save_response chiamato per sezione: {section}")

        # Estrai la keyword dai metadati se disponibile
        keyword = "unknown"
        if metadata and "keyword" in metadata:
            keyword = metadata["keyword"]
            # Sanitizza la keyword per usarla come parte del nome file
            import re
            keyword = re.sub(r'[\\/*?:"<>|]', "", keyword)
            keyword = keyword.replace(" ", "_")

        # Controlla se la risposta è vuota
        if not response:
            print(f"DEBUG: ATTENZIONE - Risposta vuota per sezione {section}")
            response = f"[Risposta vuota per sezione: {section}]"
        else:
            print(f"DEBUG: Risposta ricevuta per {section} - lunghezza: {len(response)} caratteri")
            # Mostra anteprima della risposta
            preview = response[:100].replace('\n', ' ') + ('...' if len(response) > 100 else '')
            print(f"DEBUG: Anteprima risposta: {preview}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Salva nel file principale SOVRASCRIVENDO il contenuto precedente
        try:
            # Usa 'w' invece di 'a' per sovrascrivere invece di accumulare
            with open(self.context_file, "w", encoding="utf-8") as f:
                # Prima di scrivere, controlla lo stato del file
                if os.path.exists(self.context_file):
                    print(f"DEBUG: Stato file prima della sovrascrittura - Dimensione: {os.path.getsize(self.context_file)} bytes")
                else:
                    print(f"DEBUG: Il file {self.context_file} non esiste, verrà creato")
    
                # Scrivi intestazione della sezione con keyword
                header = f"=== {section} - {keyword} - {timestamp} ===\n"
                f.write(header)
                print(f"DEBUG: Intestazione scritta: {header.strip()}")
    
                # Scrivi metadati se presenti
                if metadata:
                    metadata_text = f"Metadata: {json.dumps(metadata, indent=2)}\n"
                    f.write(metadata_text)
                    print(f"DEBUG: Metadati scritti: {len(metadata_text)} caratteri")
    
                # Scrivi la risposta
                f.write(response)
                f.write("\n\n")
                print(f"DEBUG: Risposta scritta: {len(response)} caratteri")
    
                # Verifica dopo la scrittura
                f.flush()
                print(f"DEBUG: Scrittura file completata")

            # Verifica la dimensione dopo la scrittura
            new_size = os.path.getsize(self.context_file)
            print(f"DEBUG: Dimensione file dopo la scrittura: {new_size} bytes")

        except Exception as e:
            print(f"DEBUG: ERRORE durante la scrittura sul file principale: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback:\n{traceback.format_exc()}")

        # Verifica che la directory di backup esista, se non esiste, creala
        if not self.backup_dir.exists():
            print(f"DEBUG: La directory {self.backup_dir} non esiste, verrà creata")
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                print(f"DEBUG: Directory {self.backup_dir} creata con successo")
            except Exception as e:
                print(f"DEBUG: ERRORE nella creazione della directory {self.backup_dir}: {str(e)}")

        # Crea backup con timestamp E KEYWORD (questa parte rimane invariata)
        try:
            # Crea un backup con la keyword nel nome
            backup_file = self.backup_dir / f"context_{keyword}_{timestamp}.txt"
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(f"=== BACKUP {section} - {keyword} - {timestamp} ===\n")
                if metadata:
                    f.write(f"Metadata: {json.dumps(metadata, indent=2)}\n")
                f.write(response)
            print(f"DEBUG: File di backup creato: {backup_file}")
    
            # Crea/aggiorna anche un file specifico per questa keyword (sempre sovrascritto con l'ultima risposta)
            keyword_file = self.backup_dir / f"context_{keyword}.txt"
            with open(keyword_file, "w", encoding="utf-8") as f:
                f.write(f"=== {section} - {keyword} - {timestamp} (Ultimo aggiornamento) ===\n")
                if metadata:
                    f.write(f"Metadata: {json.dumps(metadata, indent=2)}\n")
                f.write(response)
            print(f"DEBUG: File keyword-specific aggiornato: {keyword_file}")
    
        except Exception as e:
            print(f"DEBUG: ERRORE durante la creazione del backup: {str(e)}")
            import traceback
            print(f"DEBUG: Traceback:\n{traceback.format_exc()}")

        return True
    
    def upload_context(self, driver):
        """Carica il file specifico per keyword invece del contesto generale"""
        try:
            # Determina quale file caricare (preferendo il file specifico per keyword se disponibile)
            file_to_upload = self.context_file  # Default al file di contesto generale
        
            # Se disponibile, usa il file specifico per keyword dalla analisi corrente
            if hasattr(self.parent, 'current_analysis') and self.parent.current_analysis:
                # Estrai la keyword dall'analisi corrente
                keyword = None
                if 'KEYWORD' in self.parent.current_analysis:
                    keyword = self.parent.current_analysis['KEYWORD']
                elif 'project_data' in self.parent.current_analysis and 'KEYWORD' in self.parent.current_analysis['project_data']:
                    keyword = self.parent.current_analysis['project_data']['KEYWORD']
            
                # Se abbiamo trovato una keyword, cerchiamo il file specifico
                if keyword:
                    # Sanitizza la keyword per usarla nel nome file
                    import re
                    safe_keyword = re.sub(r'[\\/*?:"<>|]', "", keyword)
                    safe_keyword = safe_keyword.replace(" ", "_")
                
                    # Verifica se esiste un file specifico per questa keyword
                    keyword_file = self.backup_dir / f"context_{safe_keyword}.txt"
                    if keyword_file.exists():
                        file_to_upload = str(keyword_file)
                        self.add_log(f"🔍 Usando file contesto specifico per '{keyword}'")
                    
                        # Debug info sulla dimensione del file
                        file_size = os.path.getsize(file_to_upload)
                        self.add_log(f"📄 Dimensione file: {file_size} bytes")
                    
                        # Se il file è troppo grande, avvisa ma continua
                        if file_size > 100000:  # ~100KB
                            self.add_log(f"⚠️ Attenzione: Il file di contesto è grande ({file_size} bytes), potrebbe causare problemi")
        
            self.add_log(f"Tentativo di caricamento contesto da: {os.path.basename(file_to_upload)}")
        
            # Prova diversi selettori per il campo di upload
            selectors = [
                "div.upload-attachments.flex.items-center",
                "input[type='file']",
                "div.upload-button",
                "button[aria-label='Upload']",
                "button[aria-label='Carica']",
                "div.file-upload",
                "div.upload"
            ]
        
            # Prima di tentare il caricamento, verifica che il file esista
            if not os.path.exists(file_to_upload):
                self.add_log(f"❌ Il file {file_to_upload} non esiste, impossibile caricarlo")
                return False
            
            for selector in selectors:
                try:
                    # Cerca elementi di upload
                    upload_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if upload_elements:
                        self.add_log(f"Trovato elemento di upload con selettore: {selector}")
                    
                        # Verifica che l'elemento sia visibile e interagibile
                        if upload_elements[0].is_displayed() and upload_elements[0].is_enabled():
                            upload_elements[0].send_keys(os.path.abspath(file_to_upload))
                            self.add_log(f"File inviato all'elemento di upload")
                            time.sleep(3)  # Attendi il caricamento
                            return True
                        else:
                            self.add_log(f"Elemento trovato ma non interagibile")
                except Exception as e:
                    continue
        
            # Tenta un approccio più diretto con ricerca di input di file
            try:
                self.add_log("Tentativo con ricerca diretta di elementi input di tipo file...")
                file_inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
                if file_inputs:
                    for input_elem in file_inputs:
                        try:
                            input_elem.send_keys(os.path.abspath(file_to_upload))
                            self.add_log("File caricato tramite input file diretto")
                            time.sleep(3)
                            return True
                        except Exception:
                            continue
            except Exception:
                pass
            
            # Prova a usare JavaScript come ultimo tentativo
            try:
                self.add_log("Tentativo caricamento tramite JavaScript...")
                abs_file_path = os.path.abspath(file_to_upload).replace('\\', '\\\\')  # Escape backslashes for JS
            
                js_script = f"""
                // Crea un elemento input file nascosto
                var input = document.createElement('input');
                input.type = 'file';
                input.style.display = 'none';
                document.body.appendChild(input);
            
                // Prova a impostare il valore del file direttamente (potrebbe non funzionare per motivi di sicurezza)
                try {{
                    input.value = "{abs_file_path}";
                }} catch(e) {{
                    console.log('Impossibile impostare il valore direttamente:', e);
                }}
            
                // Simula un click sull'input per aprire il selettore di file
                input.click();
            
                // Informa l'utente
                alert('Seleziona manualmente il file: {os.path.basename(file_to_upload)}');
            
                // Monitora modifiche
                input.onchange = function() {{
                    console.log('File selezionato:', input.files[0]?.name);
                
                    // Cerca il pulsante di invio dopo la selezione del file
                    setTimeout(function() {{
                        var buttons = document.querySelectorAll('button');
                        for(var i = 0; i < buttons.length; i++) {{
                            if(buttons[i].textContent.includes('Send') || 
                               buttons[i].textContent.includes('Invia')) {{
                                buttons[i].click();
                                console.log('Pulsante di invio cliccato');
                                break;
                            }}
                        }}
                    }}, 500);
                }};
                """
            
                driver.execute_script(js_script)
                self.add_log("Script di upload eseguito, potresti dover selezionare manualmente il file")
                time.sleep(5)  # Attesa più lunga per interazione manuale
                return True
            except Exception as e:
                self.add_log(f"Errore nel tentativo JavaScript: {str(e)}")
        
            self.add_log("❌ Impossibile trovare l'elemento per il caricamento del file")
            return False
        except Exception as e:
            logging.error(f"Errore upload contesto: {str(e)}")
            self.add_log(f"❌ Errore generale nell'upload del contesto: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
            return False
    
    def handle_chat_reset(self, driver, upload_context_after_reset=False):
        """
        Gestisce il reset della chat con opzione per caricare o meno il contesto.
    
        Args:
            driver: Istanza del WebDriver di Selenium
            upload_context_after_reset: Se True, carica il contesto dopo il reset (default: False)
    
        Returns:
            str: Messaggio di stato dell'operazione
        """
        try:
            # Verifica se clear_chat è definita localmente o è una funzione importata
            if 'clear_chat' not in locals() and 'clear_chat' not in globals():
                # Se non è definita, importiamola se possibile
                try:
                    from ai_interfaces.interaction_utils import clear_chat
                except ImportError:
                    # Definizione di fallback se l'import non funziona
                    def clear_chat(driver):
                        try:
                            self.add_log("DEBUG_CHAT: Tentativo pulizia chat. URL corrente: " + driver.current_url)
                        
                            # Metodo 1: Cerca un pulsante di pulizia della chat
                            selectors = [
                                "button.clear-chat", 
                                "button[aria-label='Clear chat']",
                                "button[aria-label='Pulisci chat']",
                                ".clear-conversation-button",
                                "[data-testid='clear-chat']"
                            ]
                        
                            for selector in selectors:
                                try:
                                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                    if elements and len(elements) > 0:
                                        elements[0].click()
                                        self.add_log("DEBUG_CHAT: Pulsante di pulizia chat trovato e cliccato")
                                        time.sleep(2)
                                        return True
                                except:
                                    continue
                        
                            # Metodo 2: Prova con refresh della pagina
                            self.add_log("DEBUG_CHAT: Tentativo di refresh della pagina")
                            driver.refresh()
                            time.sleep(5)  # Attesa per caricamento pagina
                        
                            # Verifica URL dopo refresh
                            self.add_log("DEBUG_CHAT: Refresh completato, verifico URL...")
                        
                            return True
                        except Exception as e:
                            self.add_log(f"DEBUG_CHAT: Errore nella pulizia: {str(e)}")
                            return False
        
            # Esegui la pulizia della chat
            reset_success = clear_chat(driver)
        
            if reset_success:
                self.add_log("✅ Chat pulita con successo")
            
                # Carica il contesto solo se richiesto
                if upload_context_after_reset:
                    self.add_log("Tentativo di caricare il contesto dopo reset...")
                    if self.upload_context(driver):
                        self.add_log("✅ Contesto caricato con successo dopo reset")
                        return "Chat resettata e contesto ripristinato con successo"
                    else:
                        self.add_log("❌ Impossibile caricare il contesto dopo reset")
                        return "Chat resettata ma errore nel caricamento del contesto"
                else:
                    return "Chat resettata con successo (senza caricamento contesto)"
            else:
                self.add_log("❌ Errore nella pulizia della chat")
                return "Errore nella pulizia della chat"
            
        except Exception as e:
            error_msg = f"Errore nel reset della chat: {str(e)}"
            logging.error(error_msg)
            self.add_log(f"❌ {error_msg}")
        
            # Aggiungi più dettagli per il debug
            import traceback
            stack_trace = traceback.format_exc()
            self.add_log(f"Stack trace:\n{stack_trace}")
        
            return f"Errore: {str(e)}"

    def get_log_history_string(self):
        """Restituisce la cronologia dei log come stringa"""
        return "\n".join(self.log_history)
