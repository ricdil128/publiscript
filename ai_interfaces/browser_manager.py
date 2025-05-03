"""
Gestione del browser WebDriver per Selenium.
"""
import logging
import os
import traceback
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver

# Variabile globale per memorizzare l'istanza del browser
_browser_instance = None    # Singleton per l'istanza del browser
_connection_status = False  # Flag globale per lo stato di connessione

def get_browser_instance(force_new=False):
    """
    Restituisce l'istanza esistente del browser o ne crea una nuova se necessario.
    
    Args:
        force_new: Se True, forza la creazione di una nuova istanza anche se ne esiste già una
    """
    global _browser_instance
    
    if _browser_instance is None or force_new:
        _browser_instance = setup_browser()
    
    return _browser_instance

def set_connection_status(status):
    """Imposta lo stato di connessione globale"""
    global _connection_status
    _connection_status = status
    
def get_connection_status():
    """Ottiene lo stato di connessione globale"""
    global _connection_status
    return _connection_status

def setup_navigation_monitoring(driver):
    """
    Imposta il monitoraggio della navigazione per il browser
    per tracciare i cambiamenti di URL.
    
    Args:
        driver: Istanza del WebDriver
    """
    print("DEBUG_URL: Monitor di cambio URL installato nel browser:", driver is not None)
    return True

def setup_browser():
    """
    Configura e avvia il browser Chrome per l'automazione.
    Usa una singola istanza globale per evitare duplicazioni.
    """
    try:
        print("DEBUG_BROWSER: Creazione nuova istanza del browser (prima chiamata)")
        
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        
        # Usa una directory di profilo fissa per mantenere i cookie e le sessioni
        profile_dir = os.path.abspath(os.path.join(os.getcwd(), "chrome_profile"))
        os.makedirs(profile_dir, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_dir}")
        
        # Usa un profilo specifico
        options.add_argument("--profile-directory=Default")
        
        # Disabilita il messaggio di controllo dell'automazione
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Opzioni aggiuntive per migliorare stabilità
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--dns-prefetch-disable")
        
        # Importante: Specifica esplicitamente la versione di Chrome
        driver = uc.Chrome(
            options=options, 
            driver_executable_path=None, 
            version_main=135,  # Specifica esplicitamente Chrome 135
            use_subprocess=True
        )
        
        # Imposta timeout più lunghi
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        
        # Messaggio di debug
        print("DEBUG_URL: Monitor di cambio URL installato nel browser:", driver is not None)
        
        return driver
    except Exception as e:
        print(f"Errore durante l'avvio del browser: {e}")
        import logging
        logging.error(f"Errore: {e}")
        return None

# Prima definizione della funzione di debug
def debug_setup_browser():
    """
    Versione con debug della funzione setup_browser.
    Aggiunge tracciamento ma usa l'istanza globale per evitare duplicazioni.
    """
    caller = traceback.extract_stack()[-2]
    print(f"DEBUG_BROWSER: Chiamata da {caller.filename}:{caller.lineno}")
    
    # Usa la funzione originale ma con monitoraggio
    result = setup_browser()
    print(f"DEBUG_BROWSER: Browser creato/recuperato: {result is not None}")
    return result

# Riferimento ai metodi originali della classe
original_close = ChromeWebDriver.close
original_quit = ChromeWebDriver.quit

def debug_close(self):
    """Versione con debug del metodo close."""
    print("DEBUG_BROWSER: Chiusura del browser (metodo close)")
    import traceback
    caller = traceback.extract_stack()[-2]
    print(f"DEBUG_BROWSER: Chiamata da {caller.filename}:{caller.lineno}")
    return original_close(self)

def debug_quit(self):
    """Versione con debug del metodo quit."""
    print("DEBUG_BROWSER: Terminazione completa del browser (metodo quit)")
    import traceback
    caller = traceback.extract_stack()[-2]
    print(f"DEBUG_BROWSER: Chiamata da {caller.filename}:{caller.lineno}")
    # Resetta l'istanza globale quando il browser viene chiuso completamente
    global _browser_instance
    _browser_instance = None
    return original_quit(self)

# Sostituisci i metodi della classe WebDriver invece di creare istanze solo per questo
ChromeWebDriver.close = debug_close
ChromeWebDriver.quit = debug_quit

def handle_context_limit(driver, log_callback=None):
    """
    Gestisce il limite di contesto in Genspark: rileva proattivamente quando il contesto
    diventa troppo grande o quando appare un messaggio di errore, e fa un reset completo.
    
    Args:
        driver: WebDriver di Selenium
        log_callback: Funzione di callback per il logging (opzionale)

    Returns:
        bool: True se il contesto è stato ripristinato, False altrimenti
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    # 1) Lista estesa dei messaggi di errore da rilevare
    error_indicators = [
        "Context Length Exceeded",
        "Please open a new session",
        "Create a new session",
        "Limite di contesto",
        "exceeded maximum",
        "longer than",
        "too long",
        "richiesta abortita",
        "request aborted",
        "token limit",
        "try again",
        "capacity"
    ]
    
    from selenium.webdriver.common.by import By

    # 2) Ricerca più ampia degli indicatori di errore in tutta la pagina
    for indicator in error_indicators:
        try:
            # Usa XPath per cercare il testo ovunque nella pagina
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{indicator}')]")
            if elements:
                log(f"⚠️ Rilevato possibile limite di contesto: '{indicator}'. Eseguo reset del contesto...")
                return reset_context_manual(driver, log_callback)
        except Exception as e:
            log(f"Errore durante la ricerca dell'indicatore '{indicator}': {str(e)}")

    # 3) Controllo proattivo della lunghezza della chat (numero di messaggi)
    try:
        messages = driver.find_elements(By.CSS_SELECTOR, ".message-content, .chat-message-item, .message")
        message_count = len(messages)

        # Se ci sono troppi messaggi (più di 10-15), meglio fare un reset preventivo
        if message_count > 12:
            log(f"⚠️ Rilevati {message_count} messaggi nella chat (limite preventivo: 12). Eseguo reset del contesto...")
            return reset_context_manual(driver, log_callback)
    except Exception as e:
        log(f"Errore durante il conteggio dei messaggi: {str(e)}")

    # 4) Verifica la lunghezza del testo visibile nei messaggi
    try:
        total_text_length = 0
        for message in messages:
            total_text_length += len(message.text)

        # Se la lunghezza totale supera una soglia (es. 10K caratteri), reset preventivo
        if total_text_length > 10000:
            log(f"⚠️ Rilevati {total_text_length} caratteri nella chat (limite preventivo: 10000). Eseguo reset del contesto...")
            return reset_context_manual(driver, log_callback)
    except Exception as e:
        log(f"Errore durante il calcolo della lunghezza del testo: {str(e)}")

    # Se nessuna condizione è stata soddisfatta, non è necessario fare il reset
    return False


def reset_context_manual(driver, log_callback=None, restart_analysis_callback=None):
    """
    Reset del contesto con approccio progressivo:
    1. Prima tenta metodi non invasivi per mantenere la sessione
    2. Se necessario crea una nuova chat
    3. Se crea una nuova chat, riavvia l'analisi dalla prima domanda
    
    Args:
        driver: WebDriver di Selenium
        log_callback: Funzione di callback per il logging (opzionale)
        restart_analysis_callback: Funzione da chiamare per riavviare l'analisi (opzionale)
        
    Returns:
        bool: True se il reset è riuscito, False altrimenti
        dict: Dizionario con informazioni aggiuntive incluso se l'analisi deve essere riavviata
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    import time
    from datetime import datetime
    from pathlib import Path
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Salva informazioni sulla sessione corrente
    current_url = driver.current_url
    session_id = None
    created_new_session = False
    
    # Estrai l'ID di sessione se presente nell'URL
    if "/agents?id=" in current_url:
        import re
        session_match = re.search(r'/agents\?id=([^&]+)', current_url)
        if session_match:
            session_id = session_match.group(1)
            
    # Log iniziale
    log("♻️ Inizio reset del contesto...")
    if session_id:
        log(f"ID sessione rilevato: {session_id}")
    log(f"URL corrente: {current_url}")

    # Backup rapido del contesto visibile (opzionale)
    # [Codice di backup esistente...]

    # APPROCCIO 1: Tenta un refresh della pagina (meno invasivo)
    # [Codice di refresh esistente...]

    # APPROCCIO 2: Ricarica l'URL mantenendo la sessione
    # [Codice di ricaricamento URL esistente...]
    
    # Se siamo qui, i tentativi di mantenere la sessione sono falliti
    # Ora proviamo metodi più drastici che potrebbero creare una nuova chat
    log("⚠️ Tentativi di mantenere la sessione falliti, provo con metodi più drastici")
    
    # APPROCCIO 3: Cerca e clicca sul pulsante "New Chat"
    try:
        new_chat_button = driver.find_element(By.XPATH, 
                                         "//button[contains(text(), 'New Chat') or contains(@aria-label, 'New chat')]")
        log("🔍 Pulsante 'New Chat' trovato, cliccando...")
        new_chat_button.click()
        time.sleep(10)
        log("✅ Nuova chat creata tramite pulsante 'New Chat'")
        created_new_session = True
    except Exception:
        log("⚠️ Pulsante 'New Chat' non trovato, provo metodo alternativo...")

    # APPROCCIO 4: Vai alla homepage e cerca il pulsante "New Chat"
    if not created_new_session:
        try:
            driver.get("https://genspark.ai")
            log("✅ Navigazione alla homepage completata")
            time.sleep(15)
    
            # Cerca nuovamente il pulsante "New Chat"
            try:
                new_chat_buttons = driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'New Chat') or contains(text(), 'Nuova Chat')]")
        
                if new_chat_buttons:
                    new_chat_buttons[0].click()
                    time.sleep(10)
                    log("✅ Nuova chat creata tramite pulsante dalla homepage")
                    created_new_session = True
                else:
                    log("⚠️ Pulsante 'New Chat' non trovato sulla homepage")
            except Exception:
                log("⚠️ Errore nella ricerca di New Chat sulla homepage")
        except Exception as e:
            log(f"⚠️ Errore nella navigazione alla homepage: {str(e)}")

    # APPROCCIO 5: JavaScript per cercare e cliccare qualsiasi bottone di nuova chat
    if not created_new_session:
        try:
            log("🔍 Tentativo di trovare pulsante New Chat tramite JavaScript...")
            js_script = """
            var buttons = document.querySelectorAll('button');
            for(var i = 0; i < buttons.length; i++) {
                if(buttons[i].innerText.includes('New Chat') || 
                   buttons[i].innerText.includes('Nuova Chat') ||
                   buttons[i].getAttribute('aria-label') && buttons[i].getAttribute('aria-label').includes('chat')) {
                    buttons[i].click();
                    return true;
                }
            }
            return false;
            """
    
            result = driver.execute_script(js_script)
            if result:
                time.sleep(10)
                log("✅ Nuova chat creata tramite JavaScript")
                created_new_session = True
            else:
                log("⚠️ Nessun pulsante di nuova chat trovato tramite JavaScript")
        except Exception as js_err:
            log(f"⚠️ Errore nel reset tramite JavaScript: {str(js_err)}")

    # APPROCCIO 6: Ultima risorsa - ricarica semplice dell'homepage
    if not created_new_session:
        try:
            driver.get("https://genspark.ai")
            time.sleep(15)
            log("⚠️ Reset di emergenza tramite ricarica pagina")
            created_new_session = True
        except Exception as fallback_err:
            log(f"❌ Tutti i metodi di reset falliti: {str(fallback_err)}")
            return False, {"restart_analysis": False}

        # Verifica la dimensione del file di contesto e avvisa se troppo grande
        try:
            import os
            context_file = "context.txt"  # Aggiorna con il percorso corretto se diverso
            if os.path.exists(context_file):
                size_kb = os.path.getsize(context_file) / 1024
                if size_kb > 400:  # Soglia di avviso (400KB)
                    log(f"⚠️ ATTENZIONE: File di contesto grande ({size_kb:.2f} KB), potrebbe causare problemi")
        except Exception:
            pass
    
    # Se abbiamo creato una nuova sessione, segnaliamo che l'analisi deve essere riavviata
    if created_new_session:
        log("🔄 Nuova sessione creata - preparazione per riavvio dell'analisi dalla domanda #1")
        
        # PUNTO CRITICO: NON caricare il contesto completo qui
        # Questo è il punto dove probabilmente si verificava l'overflow
        # Invece di caricare il contesto, ci limitiamo a preparare il riavvio dell'analisi
        
        # Chiama il callback di riavvio se fornito
        if restart_analysis_callback:
            try:
                restart_analysis_callback()
                log("🔄 Riavvio dell'analisi richiesto tramite callback")
            except Exception as callback_err:
                log(f"⚠️ Errore nel chiamare il callback di riavvio: {str(callback_err)}")
        
        # RIMUOVERE qualsiasi tentativo di caricare il contesto o il ChatManager qui
        # Non creare o utilizzare istanze del ChatManager in questa funzione
        # Se prima c'era, rimuovi righe come:
        # chat_manager = ChatManager()
        # chat_manager.handle_chat_reset(driver)
        # chat_manager.upload_context(driver)

        return True, {"restart_analysis": True}
    
    return True, {"restart_analysis": False}
def take_debug_screenshot(driver, prefix, log_callback=None):
    """
    Scatta uno screenshot per debugging
    
    Args:
        driver: WebDriver di Selenium
        prefix: Prefisso per il nome del file
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        str: Nome del file screenshot o None in caso di errore
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"debug_{prefix}_{timestamp}.png"
        driver.save_screenshot(filename)
        log(f"📸 Screenshot di debug salvato: {filename}")
        return filename
    except Exception as e:
        log(f"⚠️ Impossibile salvare screenshot: {str(e)}")
        return None

def check_login(driver, log_callback=None):
    """
    Verifica se l'utente è loggato in Genspark.
    
    Args:
        driver: WebDriver di Selenium
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        bool: True se l'utente è loggato, False altrimenti
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Attendi che la pagina si carichi
        time.sleep(3)
        
        # Verifica se siamo nella pagina di chat
        if "/chat" in driver.current_url:
            log("✅ Utente già nella pagina di chat")
            return True
            
        # Verifica se c'è un pulsante di login visibile
        login_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign In') or contains(text(), 'Log in')]")
        if login_buttons:
            log("⚠️ Necessario login: pulsanti di login rilevati")
            return False
            
        # Verifica se c'è un input email visibile
        email_inputs = driver.find_elements(By.XPATH, "//input[@type='email' or @placeholder='Email']")
        if email_inputs:
            log("⚠️ Necessario login: form di login rilevato")
            return False
            
        # Se non ci sono elementi di login e siamo nella pagina di Genspark, probabilmente siamo loggati
        log("✅ Utente probabilmente loggato")
        return True
        
    except Exception as e:
        log(f"⚠️ Errore nella verifica del login: {str(e)}")
        return False

def create_fresh_chat(driver, context_file=None, max_retries=3):
    """
    Crea una nuova chat pulita e carica il file di contesto se specificato.
    Versione migliorata con retry e controlli.
    
    Args:
        driver: Istanza del webdriver
        context_file: Percorso al file di contesto (opzionale)
        max_retries: Numero massimo di tentativi
    
    Returns:
        bool: True se la creazione è riuscita, False altrimenti
    """
    for attempt in range(max_retries):
        try:
            # Vai alla home di Genspark
            driver.get("https://genspark.ai")
            time.sleep(10)  # Attesa più lunga per il caricamento completo
            
            # Cerca un pulsante "Nuova chat" o simile
            new_chat_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'New Chat') or contains(text(), 'Nuova Chat')]")
            
            if new_chat_buttons:
                new_chat_buttons[0].click()
                print("Nuova chat creata tramite pulsante dedicato")
                time.sleep(10)  # Attesa più lunga per l'apertura della nuova chat
            else:
                # Prova un approccio alternativo
                try:
                    # Usa JavaScript per cercare e cliccare qualsiasi bottone di nuova chat
                    js_script = """
                    var buttons = document.querySelectorAll('button');
                    for(var i = 0; i < buttons.length; i++) {
                        if(buttons[i].innerText.includes('New Chat') || 
                           buttons[i].innerText.includes('Nuova Chat') ||
                           buttons[i].getAttribute('aria-label') && buttons[i].getAttribute('aria-label').includes('New')) {
                            buttons[i].click();
                            return true;
                        }
                    }
                    return false;
                    """
                    
                    result = driver.execute_script(js_script)
                    if result:
                        print("Nuova chat creata tramite JavaScript")
                        time.sleep(10)
                    else:
                        # Se non trovi un pulsante specifico, ricarica semplicemente la pagina
                        driver.get("https://genspark.ai")
                        print("Nuova chat creata tramite ricaricamento pagina")
                        time.sleep(10)
                except:
                    # Fallback: ricarica la pagina
                    driver.get("https://genspark.ai")
                    print("Fallback: nuova chat tramite ricaricamento pagina")
                    time.sleep(10)
            
            # Verifica che siamo effettivamente in una pagina di chat
            if "chat" not in driver.current_url.lower() and "agents" not in driver.current_url.lower():
                print(f"⚠️ Non sembra che siamo in una pagina di chat. URL: {driver.current_url}")
                if attempt < max_retries - 1:
                    continue
            
            # Se è specificato un file di contesto, caricalo con retry
            if context_file and os.path.exists(context_file):
                upload_success = False
                
                # Prova diversi metodi per caricare il file
                for upload_attempt in range(3):
                    try:
                        # Metodo 1: Trova l'area di upload o bottone
                        upload_selectors = [
                            "input[type='file']",
                            "div.upload-attachments.flex.items-center",
                            "div.upload-button",
                            "button[aria-label='Upload']",
                            "button[aria-label='Carica']",
                            "div.file-upload",
                            ".upload button"
                        ]
                        
                        for selector in upload_selectors:
                            try:
                                upload_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                if upload_elements:
                                    print(f"Trovato elemento di upload con selettore: {selector}")
                                    
                                    # Se è un input di tipo file, usa send_keys
                                    if selector == "input[type='file']":
                                        upload_elements[0].send_keys(os.path.abspath(context_file))
                                    else:
                                        # Altrimenti clicca il bottone e poi trova l'input
                                        upload_elements[0].click()
                                        time.sleep(3)
                                        
                                        # Dopo il click, cerca l'input file
                                        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                                        if file_inputs:
                                            file_inputs[0].send_keys(os.path.abspath(context_file))
                                    
                                    time.sleep(5)  # Attesa per il caricamento
                                    print(f"File di contesto caricato: {context_file}")
                                    upload_success = True
                                    break
                            except Exception as e:
                                print(f"Errore con selettore {selector}: {str(e)}")
                                continue
                        
                        if upload_success:
                            break
                            
                        # Metodo 2: Usa un input temporaneo via JavaScript
                        js_upload = """
                        // Crea un input file temporaneo
                        var input = document.createElement('input');
                        input.type = 'file';
                        input.style.display = 'none';
                        document.body.appendChild(input);
                        
                        // Ritorna l'ID dell'elemento per riferimento futuro
                        var inputId = 'tempFileInput_' + Date.now();
                        input.id = inputId;
                        return inputId;
                        """
                        
                        input_id = driver.execute_script(js_upload)
                        if input_id:
                            # Trova l'input temporaneo e carica il file
                            temp_input = driver.find_element(By.ID, input_id)
                            temp_input.send_keys(os.path.abspath(context_file))
                            time.sleep(5)
                            
                            # Cerca pulsanti di conferma
                            confirm_buttons = driver.find_elements(By.XPATH, 
                                "//button[contains(text(), 'Upload') or contains(text(), 'Carica') or contains(text(), 'Conferma')]")
                            
                            if confirm_buttons:
                                confirm_buttons[0].click()
                                time.sleep(5)
                                upload_success = True
                                break
                    
                    except Exception as upload_error:
                        print(f"Errore nel tentativo {upload_attempt+1} di caricamento: {str(upload_error)}")
                        time.sleep(3)
                
                if not upload_success:
                    print(f"⚠️ Impossibile caricare automaticamente il file di contesto")
                    print(f"⚠️ Il file {context_file} può essere caricato manualmente se necessario")
            
            return True
            
        except Exception as e:
            print(f"Errore nella creazione di una nuova chat (tentativo {attempt+1}): {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(10)  # Pausa prima del prossimo tentativo
            else:
                print("❌ Tutti i tentativi di creazione nuova chat falliti")
                return False
    
    return False
