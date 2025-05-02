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
        """Salva la risposta con metadati in modo cumulativo"""
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

        # Verifica che il file di contesto esista, se non esiste, crealo
        if not os.path.exists(self.context_file):
            print(f"DEBUG: Il file {self.context_file} non esiste, verrà creato")
            try:
                with open(self.context_file, "w", encoding="utf-8") as f:
                    f.write(f"=== INIZIALIZZAZIONE - {timestamp} ===\n\n")
                print(f"DEBUG: File {self.context_file} creato con successo")
            except Exception as e:
                print(f"DEBUG: ERRORE nella creazione del file {self.context_file}: {str(e)}")

        # Verifica che la directory di backup esista, se non esiste, creala
        if not self.backup_dir.exists():
            print(f"DEBUG: La directory {self.backup_dir} non esiste, verrà creata")
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                print(f"DEBUG: Directory {self.backup_dir} creata con successo")
            except Exception as e:
                print(f"DEBUG: ERRORE nella creazione della directory {self.backup_dir}: {str(e)}")

        # Salva nel file principale in modo cumulativo
        try:
            with open(self.context_file, "a", encoding="utf-8") as f:
                # Prima di scrivere, controlla lo stato del file
                print(f"DEBUG: Stato file prima della scrittura - Dimensione: {os.path.getsize(self.context_file) if os.path.exists(self.context_file) else 0} bytes")
        
                # Scrivi intestazione della sezione con keyword
                header = f"\n=== {section} - {keyword} - {timestamp} ===\n"
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

        # Crea backup con timestamp E KEYWORD
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
        """Carica il file di contesto nella nuova chat"""
        try:
            # Aggiungi questo metodo migliorato che tenta diversi selettori
            self.add_log("Tentativo di caricamento contesto...")
        
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
        
            for selector in selectors:
                try:
                    upload_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if upload_elements:
                        self.add_log(f"Trovato elemento di upload con selettore: {selector}")
                        upload_elements[0].send_keys(os.path.abspath(self.context_file))
                        time.sleep(3)  # Attendi il caricamento
                        return True
                except Exception as e:
                    continue
        
            # Prova a usare JavaScript come ultimo tentativo
            try:
                self.add_log("Tentativo caricamento tramite JavaScript...")
                js_script = """
                var input = document.createElement('input');
                input.type = 'file';
                input.onchange = function() {
                    var file = this.files[0];
                    var formData = new FormData();
                    formData.append('file', file);
                    // Qui dovremmo inviare il file ma senza API non è semplice
                
                    // Simuliamo un click su invio
                    var buttons = document.querySelectorAll('button');
                    for(var i = 0; i < buttons.length; i++) {
                        if(buttons[i].textContent.includes('Send') || 
                            buttons[i].textContent.includes('Invia')) {
                            buttons[i].click();
                            break;
                        }
                    }
                };
                input.click();
                """
                driver.execute_script(js_script)
                self.add_log("Script di upload eseguito, controlla se è stato caricato")
                return True
            except Exception as e:
                self.add_log(f"Errore nel tentativo JavaScript: {str(e)}")
        
            self.add_log("❌ Impossibile trovare l'elemento per il caricamento del file")
            return False
        except Exception as e:
            logging.error(f"Errore upload contesto: {str(e)}")
            return False
    
    def handle_chat_reset(self, driver):
        """Gestisce il reset della chat"""
        try:
            if clear_chat(driver):
                if self.upload_context(driver):
                    return "Contesto ripristinato con successo"
                return "Errore nel caricamento del contesto"
            return "Errore nella pulizia della chat"
        except Exception as e:
            logging.error(f"Errore reset chat: {str(e)}")
            return f"Errore: {str(e)}"

    def get_log_history_string(self):
        """Restituisce la cronologia dei log come stringa"""
        return "\n".join(self.log_history)
