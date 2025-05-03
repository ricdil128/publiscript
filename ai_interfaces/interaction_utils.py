"""
Utilità per interazione con Genspark.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException

def get_input_box(driver, max_attempts=5):
    """
    Recupera la casella di input nella chat in modo affidabile,
    con tentativi multipli e diverse strategie.
    
    Args:
        driver: Istanza del webdriver
        max_attempts: Numero massimo di tentativi
        
    Returns:
        WebElement: Elemento input box o None se non trovato
    """
    for attempt in range(max_attempts):
        try:
            # Strategia 1: Selettore CSS standard
            input_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper textarea"))
            )
            
            # Pulisci l'input con retry
            for _ in range(3):
                try:
                    input_box.clear()
                    time.sleep(0.5)
                    
                    # Conferma che sia effettivamente vuoto
                    value = input_box.get_attribute("value")
                    if not value:
                        return input_box
                except:
                    pass
            
            # Se non riesci a pulirlo ma l'hai trovato, restituiscilo comunque
            return input_box
            
        except:
            # Strategia 2: Selettori alternativi
            selectors = [
                "textarea[placeholder]",
                ".chat-input textarea",
                "[role='textbox']",
                "form textarea"
            ]
            
            for selector in selectors:
                try:
                    input_box = driver.find_element(By.CSS_SELECTOR, selector)
                    if input_box.is_displayed() and input_box.is_enabled():
                        input_box.clear()
                        time.sleep(0.5)
                        return input_box
                except:
                    pass
            
            # Strategia 3: Se non trova nulla, prova a cliccare nell'area di input
            try:
                # Cerca l'area dell'input senza cercare specificamente la textarea
                input_area = driver.find_element(By.CSS_SELECTOR, "div.search-input-wrapper")
                if input_area:
                    # Clicca al centro dell'area
                    action = ActionChains(driver)
                    action.move_to_element(input_area).click().perform()
                    time.sleep(1)
                    
                    # Cerca nuovamente l'input box
                    input_box = driver.find_element(By.CSS_SELECTOR, "div.search-input-wrapper textarea")
                    if input_box:
                        return input_box
            except:
                pass
        
        # Se non trova ancora l'input box, attendi e riprova
        print(f"⚠️ Input box non trovato, tentativo {attempt+1}/{max_attempts}")
        time.sleep(3)
    
    # Se tutti i tentativi falliscono
    print("❌ Impossibile trovare l'input box dopo tutti i tentativi")
    return None

def clear_chat(driver, max_attempts=3):
    """
    Pulisce la chat in modo affidabile usando un approccio progressivo,
    mantenendo sempre la sessione corrente.
    
    Args:
        driver: Il driver Selenium WebDriver
        max_attempts: Numero massimo di tentativi per metodo
        
    Returns:
        bool: True se la pulizia è riuscita, False altrimenti
    """
    # Salva l'URL corrente e l'ID sessione per riferimento
    current_url = driver.current_url
    session_id = None
    
    # Estrai l'ID di sessione se presente nell'URL
    if "/agents?id=" in current_url:
        import re
        session_match = re.search(r'/agents\?id=([^&]+)', current_url)
        if session_match:
            session_id = session_match.group(1)
            
    # Log per debug
    print(f"DEBUG_CHAT: Tentativo pulizia chat. URL corrente: {current_url}")
    
    # Import necessari
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    
    # LIVELLO 1: Metodi standard UI
    # ---------------------------------
    
    # Metodo 1: Pulsante "Clear chat"
    for attempt in range(max_attempts):
        try:
            clear_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Clear chat']")
            if clear_buttons:
                print("DEBUG_CHAT: Trovato pulsante 'Clear chat', cliccando...")
                clear_buttons[0].click()
                time.sleep(5)
                
                # Verifica se la chat è stata pulita
                messages = driver.find_elements(By.CSS_SELECTOR, "div.chat-message-item")
                if not messages:
                    print("DEBUG_CHAT: Pulizia riuscita con pulsante 'Clear chat'")
                    return True
            
            # Se sono ancora presenti messaggi, prova con la conferma di pulizia
            confirm_buttons = driver.find_elements(By.CSS_SELECTOR, "button.confirm-button")
            if confirm_buttons:
                print("DEBUG_CHAT: Trovato pulsante conferma pulizia, cliccando...")
                confirm_buttons[0].click()
                time.sleep(3)
                return True
        except Exception as e:
            print(f"DEBUG_CHAT: Errore nel metodo Clear chat: {str(e)}")
    
    # Metodo 2: Cerca pulsanti di pulizia tramite testo
    for attempt in range(max_attempts):
        try:
            clear_text_buttons = driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Clear') or contains(@aria-label, 'Clear')]")
            if clear_text_buttons:
                print("DEBUG_CHAT: Trovato pulsante con testo 'Clear', cliccando...")
                clear_text_buttons[0].click()
                time.sleep(5)
                return True
        except Exception as e:
            print(f"DEBUG_CHAT: Errore nel metodo testo Clear: {str(e)}")
    
    # Metodo 3: JavaScript per trovare e cliccare pulsanti di pulizia
    for attempt in range(max_attempts):
        try:
            js_result = driver.execute_script("""
                // Cerca pulsanti di pulizia
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if ((buttons[i].textContent && buttons[i].textContent.toLowerCase().includes('clear')) || 
                        (buttons[i].getAttribute('aria-label') && 
                         buttons[i].getAttribute('aria-label').toLowerCase().includes('clear'))) {
                        buttons[i].click();
                        return true;
                    }
                }
                
                // Cerca icone o link che potrebbero pulire la chat
                var icons = document.querySelectorAll('i, svg, a');
                for (var i = 0; i < icons.length; i++) {
                    var title = icons[i].getAttribute('title') || 
                               icons[i].getAttribute('aria-label') || 
                               icons[i].getAttribute('alt') || '';
                    if (title.toLowerCase().includes('clear') || 
                        title.toLowerCase().includes('trash') || 
                        title.toLowerCase().includes('delete')) {
                        icons[i].click();
                        return true;
                    }
                }
                
                return false;
            """)
            
            if js_result:
                print("DEBUG_CHAT: Pulizia chat tramite JavaScript riuscita")
                time.sleep(5)
                return True
        except Exception as e:
            print(f"DEBUG_CHAT: Errore nel metodo JavaScript: {str(e)}")
    
    # Metodo 4: Prova con il pulsante Home con ritorno alla chat
    for attempt in range(max_attempts):
        try:
            home_buttons = driver.find_elements(By.CSS_SELECTOR, "a[aria-label='Home']") or \
                          driver.find_elements(By.XPATH, "//a[contains(., 'Home')]")
            if home_buttons:
                print("DEBUG_CHAT: Provo con il pulsante Home e ritorno alla chat")
                home_buttons[0].click()
                time.sleep(8)
                
                # Torna alla sessione originale
                if session_id:
                    print(f"DEBUG_CHAT: Ritorno alla sessione: {session_id}")
                    driver.get(f"https://www.genspark.ai/agents?id={session_id}")
                    
                    # Attendi che la pagina sia completamente caricata
                    try:
                        WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea"))
                        )
                        print("DEBUG_CHAT: Ritorno alla chat riuscito")
                        return True
                    except:
                        print("DEBUG_CHAT: Timeout nel ritorno alla chat")
        except Exception as e:
            print(f"DEBUG_CHAT: Errore nel metodo Home: {str(e)}")
    
    # LIVELLO 2: Refresh della pagina corrente
    # ---------------------------------
    print("DEBUG_CHAT: Tentativo di refresh della pagina")
    try:
        # Salva l'URL corrente prima del refresh
        pre_refresh_url = driver.current_url
        
        # Esegui il refresh
        driver.refresh()
        
        # Attendi che la pagina sia caricata
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, .input-box"))
            )
            print("DEBUG_CHAT: Refresh completato, verifico URL...")
            
            # Verifica che l'URL post-refresh sia coerente
            post_refresh_url = driver.current_url
            if session_id and session_id not in post_refresh_url:
                print(f"DEBUG_CHAT: Sessione persa dopo refresh, ripristino: {session_id}")
                driver.get(f"https://www.genspark.ai/agents?id={session_id}")
                time.sleep(10)
            
            return True
            
        except Exception as wait_err:
            print(f"DEBUG_CHAT: Timeout nell'attesa post-refresh: {str(wait_err)}")
    except Exception as refresh_err:
        print(f"DEBUG_CHAT: Errore durante il refresh: {str(refresh_err)}")
    
    # LIVELLO 3: Ricarica l'URL mantenendo la sessione
    # ---------------------------------
    if session_id:
        try:
            target_url = f"https://www.genspark.ai/agents?id={session_id}"
            print(f"DEBUG_CHAT: Ricarico esplicitamente l'URL sessione: {target_url}")
            driver.get(target_url)
            
            # Attendi che la pagina sia caricata
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, .input-box"))
                )
                print("DEBUG_CHAT: Ricaricamento URL sessione riuscito")
                return True
            except:
                print("DEBUG_CHAT: Timeout nel caricamento URL sessione")
        except Exception as e:
            print(f"DEBUG_CHAT: Errore nel ricaricamento URL sessione: {str(e)}")
    else:
        print("DEBUG_CHAT: Impossibile ricaricare URL sessione (ID sessione non disponibile)")
    
    # Se arriviamo qui, nessun metodo è riuscito a pulire la chat
    print("DEBUG_CHAT: Impossibile pulire la chat con tutti i metodi disponibili")
    return False


def is_chat_empty(driver):
    """
    Verifica se la chat è vuota (nessun messaggio presente).
    
    Args:
        driver: Il driver Selenium WebDriver
        
    Returns:
        bool: True se la chat è vuota, False altrimenti
    """
    try:
        from selenium.webdriver.common.by import By
        
        # Prova diversi selettori per cercare i messaggi
        selectors = [
            "div.chat-message-item",
            ".message-content",
            "div.chat-wrapper div.desc > div > div > div"
        ]
        
        # Se troviamo messaggi con uno qualsiasi dei selettori, la chat non è vuota
        for selector in selectors:
            messages = driver.find_elements(By.CSS_SELECTOR, selector)
            if messages and len(messages) > 0:
                return False
        
        # Se non abbiamo trovato messaggi con nessun selettore, la chat è vuota
        return True
    except:
        # In caso di errore, assumiamo che la chat non sia vuota
        return False

def get_ai_response(driver):
    """
    Recupera l'ultima risposta generata dall'AI nell'interfaccia di Genspark.
    Utilizza metodi multipli per massimizzare l'affidabilità.
    
    Args:
        driver: Istanza Selenium WebDriver
        
    Returns:
        str: Testo della risposta o stringa vuota se non trovata
    """
    # Lista di selettori per trovare le risposte dell'AI (dal più al meno specifico)
    response_selectors = [
        "div.agent-turn div.message", # Selettore specifico per i turni dell'AI
        "div[data-message-author-role='assistant']", # Attributo specifico dell'AI
        "div.chat-wrapper div.message:nth-child(even)", # Assumendo che l'AI sia nei messaggi pari
        ".markdown-wrapper", # Contenitore markdown tipico delle risposte AI
        "div.chat-wrapper div.desc > div > div > div" # Selettore generico fallback
    ]
    
    # Prova tutti i selettori
    for selector in response_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                # Prendi l'ultimo elemento (risposta più recente)
                last_response = elements[-1].text.strip()
                if last_response and len(last_response) > 10:  # Ignora risposte troppo corte
                    print(f"DEBUG: Risposta trovata con selettore '{selector}': {len(last_response)} caratteri")
                    return last_response
        except Exception:
            continue
    
    # Se i selettori falliscono, prova con JavaScript più complesso
    try:
        js_script = """
        // Funzione per trovare l'ultimo messaggio dell'assistente
        function findLastAssistantMessage() {
            // Cerca diversi tipi di container per i messaggi
            const messageContainers = [
                // Turni dell'assistente
                Array.from(document.querySelectorAll('.agent-turn')),
                // Elementi con attributo specifico dell'assistente
                Array.from(document.querySelectorAll('[data-message-author-role="assistant"]')),
                // Struttura generica dei messaggi
                Array.from(document.querySelectorAll('.message-content'))
            ];
            
            // Cerca in ciascun tipo di container
            for (const containers of messageContainers) {
                if (containers.length > 0) {
                    // Prendi l'ultimo messaggio
                    const lastMsg = containers[containers.length - 1];
                    if (lastMsg && lastMsg.textContent && lastMsg.textContent.trim().length > 10) {
                        return lastMsg.textContent.trim();
                    }
                }
            }
            
            // Fallback: cerca tutti i div con classe text o content che potrebbero contenere messaggi
            const textDivs = Array.from(document.querySelectorAll('div.text, div.content'));
            if (textDivs.length > 0) {
                // Prendi l'ultimo div che potrebbe essere la risposta
                const lastDiv = textDivs[textDivs.length - 1];
                if (lastDiv && lastDiv.textContent && lastDiv.textContent.trim().length > 10) {
                    return lastDiv.textContent.trim();
                }
            }
            
            return null;
        }
        
        return findLastAssistantMessage();
        """
        
        js_response = driver.execute_script(js_script)
        if js_response and len(js_response) > 10:
            print(f"DEBUG: Risposta recuperata via JavaScript: {len(js_response)} caratteri")
            return js_response
    except Exception:
        pass
    
    # Se tutto fallisce, prova un'ultima strategia disperata
    try:
        # Cerca qualsiasi elemento di testo che potrebbe essere una risposta
        all_text_elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(), '.') and not(ancestor::button) and not(ancestor::input)]")
        
        # Filtra gli elementi in base alla dimensione del testo
        potential_responses = [el.text for el in all_text_elements 
                              if el.text and len(el.text.strip()) > 50]
        
        if potential_responses:
            # Prendi la risposta più lunga come probabile risposta dell'AI
            longest_response = max(potential_responses, key=len)
            print(f"DEBUG: Risposta recuperata via strategia fallback: {len(longest_response)} caratteri")
            return longest_response
    except Exception:
        pass
    
    return ""  # Nessuna risposta trovata

def send_prompt_and_wait_for_response(driver, input_box, full_prompt, max_retries=3):
    """
    Invia un prompt a Genspark, attende e recupera la risposta con backoff esponenziale.
    La funzione attende le parole 'FINE' o 'FINE_RISPOSTA' come segnale di completamento.
    
    Args:
        driver: Istanza del webdriver
        input_box: Elemento di input
        full_prompt: Testo del prompt
        max_retries: Numero massimo di tentativi (default: 3)
        
    Returns:
        str: Risposta da Genspark
    """
    for retry_count in range(max_retries + 1):  # +1 perché il primo non è un retry
        if retry_count > 0:
            # Backoff esponenziale: attesa più lunga ad ogni tentativo
            wait_time = 15 * (2 ** retry_count)  # 30s, 60s, 120s
            print(f"Ritentativo {retry_count}/{max_retries} per risposta abortita... attendo {wait_time} secondi")
            time.sleep(wait_time)
            
            # Pulisci la chat prima di riprovare
            try:
                clear_chat(driver)
                time.sleep(10)  # Aumentato il tempo dopo clear_chat
            except:
                # Se non riesci a pulire la chat, ricarica la pagina
                driver.get("https://genspark.ai")
                time.sleep(15)  # Aumentato il tempo dopo refresh pagina
                # Ottieni nuovamente l'input box
                input_box = get_input_box(driver)
                
        # Aggiunge la richiesta di scrivere FINE_RISPOSTA alla fine della risposta
        prompt_to_send = full_prompt + "\n\nPer favore, scrivi la parola 'FINE_RISPOSTA' su una nuova riga quando hai completato la tua risposta."
        
        # Pulizia e suddivisione del testo
        clean_prompt = clean_text(prompt_to_send)
        chunks = split_text(clean_prompt, chunk_size=800)  # Ridotto chunk_size per evitare sovraccarichi
        
        # Invio del prompt in blocchi con pause tra ogni blocco
        for chunk_index, chunk in enumerate(chunks):
            input_box.clear()
            time.sleep(1)  # Pausa prima di inserire testo
            
            # Digitazione carattere per carattere per maggiore stabilità
            for char in chunk:
                input_box.send_keys(char)
                time.sleep(0.01)  # Aumentato leggermente il delay tra caratteri
            
            # Pausa più lunga tra i chunk
            if chunk_index < len(chunks) - 1:
                time.sleep(3)  # Pausa tra i chunk
            else:
                time.sleep(2)  # Pausa finale
        
        # Invio del prompt con tentativi multipli
        send_success = False
        for send_attempt in range(3):
            try:
                send_button = driver.find_element(By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon")
                send_button.click()
                send_success = True
                print(f"Invio riuscito al tentativo {send_attempt+1}")
                break
            except:
                if send_attempt < 2:  # Se non è l'ultimo tentativo
                    time.sleep(2)
                    try:
                        # Prova con l'invio da tastiera come alternativa
                        input_box.send_keys(Keys.RETURN)
                        send_success = True
                        print("Invio riuscito tramite tasto Return")
                        break
                    except:
                        pass

        if not send_success:
            print("Tutti i tentativi di invio falliti")
            if retry_count < max_retries:
                continue
            else:
                return "Errore: Impossibile inviare il messaggio"
    
        # Attesa iniziale più lunga per l'inizio della risposta
        time.sleep(20)
    
        # Sistema di attesa con cicli multipli e stabilità
        attempt = 0
        max_attempts = 45  # Aumentato il numero massimo di tentativi (~15 minuti)
        current_response = ""
        response_complete = False
        total_cycles = 0
        max_cycles = 5  # Aumentato il numero di cicli
        request_aborted = False
        last_length = 0
        stable_count = 0
        
        # Loop per attendere il completamento della risposta
        while total_cycles < max_cycles and not response_complete and not request_aborted:
            attempt = 0
            print(f"\nCiclo di attesa {total_cycles + 1}/{max_cycles}")
            
            while attempt < max_attempts and not response_complete and not request_aborted:
                try:
                    # Controlla se è necessario gestire il limite di contesto
                    if attempt % 5 == 0 and attempt > 0:
                        # Implementa qui la logica per gestire il limite di contesto se necessario
                        pass
                    
                    # Cerca messaggi nella chat
                    messages = driver.find_elements(By.CSS_SELECTOR, ".message-content")
                    if messages:
                        for message in reversed(messages):
                            text = message.text.strip()
                            if text:
                                current_response = text
                                
                                # Verifica esplicita per problemi comuni
                                if "Richiesta abortita" in current_response or "request aborted" in current_response.lower():
                                    print("Messaggio 'Richiesta abortita' rilevato. Avvio nuovo tentativo...")
                                    request_aborted = True
                                    break
                                
                                # Verifica se la risposta contiene "FINE" o "FINE_RISPOSTA" alla fine
                                if "FINE_RISPOSTA" in current_response:
                                    response_complete = True
                                    # Rimuove la parola "FINE_RISPOSTA" dalla risposta finale
                                    current_response = current_response.split("FINE_RISPOSTA")[0].strip()
                                    print("Parola FINE_RISPOSTA trovata! Elaborazione completata.")
                                    break
                                elif "FINE" in current_response:
                                    response_complete = True
                                    # Rimuove la parola "FINE" dalla risposta finale
                                    current_response = current_response.split("FINE")[0].strip()
                                    print("Parola FINE trovata! Elaborazione completata.")
                                    break
                                
                                # Verifica stabilità della risposta
                                current_length = len(current_response)
                                if current_length == last_length:
                                    stable_count += 1
                                    if stable_count >= 5:  # Richiede 5 cicli di stabilità
                                        print(f"Risposta stabile dopo {attempt} tentativi. Considerata completa.")
                                        response_complete = True
                                        break
                                else:
                                    stable_count = 0
                                    last_length = current_length
    
                    # Attesa adattiva: più lunga all'inizio, più breve man mano che passa il tempo
                    wait_time = max(5, 20 - attempt // 3)  # Da 20s a 5s
                    time.sleep(wait_time)
                    attempt += 1
                    
                    # Log periodico
                    if attempt % 5 == 0:  # Ogni 5 tentativi
                        if current_response:
                            print(f"In attesa del completamento... ({attempt}/{max_attempts}) - {len(current_response)} caratteri finora")
                        else:
                            print(f"In attesa della risposta... ({attempt}/{max_attempts})")
    
                except StaleElementReferenceException:
                    # Gestione errore elementi non più validi (pagina aggiornata)
                    time.sleep(5)
                    attempt += 1
    
            # Se abbiamo rilevato "Richiesta abortita", esci subito dal ciclo interno
            if request_aborted:
                break
                
            # Se non completato in questo ciclo, prova un altro ciclo
            if not response_complete:
                if total_cycles < max_cycles - 1:
                    print(f"FINE/FINE_RISPOSTA non trovata nel ciclo {total_cycles + 1}. Avvio nuovo ciclo di attesa...")
                    time.sleep(10)  # Pausa più lunga tra i cicli
                total_cycles += 1
    
        # Se la richiesta è stata abortita, passa direttamente al prossimo tentativo
        if request_aborted:
            # Se non è l'ultimo tentativo, continua con il prossimo
            if retry_count < max_retries:
                continue
            else:
                print("ATTENZIONE: 'Richiesta abortita' rilevata in tutti i tentativi.")
                return "Errore: Richiesta abortita ripetutamente dopo tutti i tentativi."
    
        # Se abbiamo una risposta completa, restituiscila
        if response_complete:
            return current_response
        
        # Se abbiamo comunque una risposta di lunghezza ragionevole, uso quella
        if current_response and len(current_response) > 200:
            print("Risposta non completata con FINE ma di lunghezza ragionevole, la uso comunque")
            return current_response
            
        # Altrimenti, se non è l'ultimo tentativo, riprova
        if retry_count < max_retries:
            print(f"Risposta incompleta dopo tutti i cicli. Tentativo {retry_count+1} in corso...")
            # Continua con il prossimo ciclo di retry
        else:
            # È l'ultimo tentativo, gestisci manualmente o restituisci la risposta parziale
            print("ATTENZIONE: Le parole FINE o FINE_RISPOSTA non sono state rilevate dopo tutti i tentativi.")
            print("Verificare manualmente se la risposta è completa.")
            
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, ".message-content")
                if messages:
                    for message in reversed(messages):
                        text = message.text.strip()
                        if text:
                            current_response = text
                            if "FINE_RISPOSTA" in current_response:
                                current_response = current_response.split("FINE_RISPOSTA")[0].strip()
                            elif "FINE" in current_response:
                                current_response = current_response.split("FINE")[0].strip()
                            break
            except:
                pass
    
    return current_response if current_response else "Errore: Nessuna risposta trovata."

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

def send_to_genspark(self, text, prompt_id=None, section_number=None):
        """
        Invia un messaggio a Genspark e attende la risposta.
        Versione completamente rivista per garantire stabilità e affidabilità,
        con aggiornamento dell'interfaccia utente integrato.
        """
        self.cooldown_manager.track_request()

        # Log iniziale con posizione nel flusso
        location = self.log_prompt_location(
            prompt_id or "unknown",
            section_number or "unknown",
            f"Invio testo ({len(text)} caratteri)"
        )

        # Log di debug per tracciare l'esecuzione
        print(f"DEBUG: send_to_genspark chiamato - prompt_id: {prompt_id}, section_number: {section_number}")
        print(f"DEBUG: Lunghezza testo da inviare: {len(text)} caratteri")
        print(f"DEBUG: Anteprima testo: {text[:150].replace(chr(10), ' ')}...")

        # Funzione helper interna per aggiornare UI e restituire la risposta
        def update_ui_and_return(response, success=True, message=None):
            """Helper interno per aggiornare UI e tornare la risposta"""
            # Debug della risposta
            if response:
                print(f"DEBUG: Salvataggio risposta - Lunghezza: {len(response)}")
                print(f"DEBUG: Preview risposta: {response[:200].replace(chr(10), ' ')}...")
            
                # Controlla se la risposta contiene FINE o FINE_RISPOSTA
                has_end = "FINE_RISPOSTA" in response or "FINE" in response
                print(f"DEBUG: Risposta contiene terminatore: {has_end}")
            
                # Se la risposta è completa, salvala nel file di contesto
                if hasattr(self, 'chat_manager'):
                    print(f"DEBUG: Chiamata a chat_manager.save_response per {location}")
                    metadata = {
                        "prompt_id": prompt_id,
                        "section_number": section_number,
                        "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S'),
                        "has_terminator": has_end
                    }
                    # Verifica se il file di contesto esiste prima di salvare
                    context_file = getattr(self.chat_manager, 'context_file', 'context.txt')
                    print(f"DEBUG: Verifica file context.txt - Esiste: {os.path.exists(context_file)}")
                
                    # Salva la risposta
                    try:
                        self.chat_manager.save_response(response, f"Prompt {prompt_id}-{section_number}", metadata)
                        print(f"DEBUG: Risposta salvata con successo in {context_file}")
                    except Exception as save_error:
                        print(f"DEBUG: ERRORE durante il salvataggio della risposta: {str(save_error)}")
                        import traceback
                        print(f"DEBUG: Traceback salvataggio:\n{traceback.format_exc()}")
            else:
                print("DEBUG: Risposta vuota o None")
            
            if hasattr(self, 'results_display') and response:
                try:
                    # Per risposte brevi o in caso di errore, formattazione semplice
                    if len(response) < 2000 or not success:
                        status_class = "bg-green-50 border-green-500" if success else "bg-red-50 border-red-500"
                        status_text = "Risposta completata" if success else f"Errore: {message or 'Vedi dettagli nel log'}"
                
                        html_response = f"""
                        <div class="{status_class} border-l-4 p-3 mb-3 rounded">
                            <div class="flex justify-between">
                                <div><strong>{status_text}</strong></div>
                                <div>{len(response)} caratteri</div>
                            </div>
                        </div>
                        <div class="results-content p-4 bg-white rounded-lg border border-gray-200">
                            <pre style="white-space: pre-wrap; font-family: monospace;">{response}</pre>
                        </div>
                        """
                    else:
                        # Per risposte lunghe, mostra anteprima e aggiungi opzione per vedere tutto
                        preview = response[:1000] + "..." 
                        html_response = f"""
                        <div class="bg-green-50 border-l-4 border-green-500 p-3 mb-3 rounded">
                            <div class="flex justify-between">
                                <div><strong>Risposta completata</strong></div>
                                <div>{len(response)} caratteri</div>
                            </div>
                        </div>
                        <div class="results-preview p-4 bg-white rounded-lg border border-gray-200">
                            <pre style="white-space: pre-wrap; font-family: monospace; max-height: 300px; overflow-y: auto;">{preview}</pre>
                            <div class="mt-2 text-center">
                                <em class="text-gray-500">Risposta completa salvata - Clicca "Completa Analisi" per vedere i risultati formattati</em>
                            </div>
                        </div>
                        """
            
                    self.results_display.update(value=html_response)
                    self.add_log(f"✅ Interfaccia aggiornata con risposta di {len(response)} caratteri")
                    print(f"DEBUG: UI aggiornata con risposta di {len(response)} caratteri")
                except Exception as ui_error:
                    self.add_log(f"❌ Errore nell'aggiornamento dell'interfaccia: {str(ui_error)}")
                    print(f"DEBUG: Errore nell'aggiornamento UI: {str(ui_error)}")
    
            return response

        # Log iniziale con stack trace per debugging
        import traceback
        call_stack = traceback.format_stack()
        stack_info = "\n".join(call_stack[-5:])

        self.add_log(f"🔍 [{location}] Inizio invio prompt")
        self.add_log(f"🔍 Inizio invio prompt ({len(text)} caratteri) in {location}")

        # Verifica che il browser sia attivo
        from ai_interfaces.browser_manager import get_browser_instance, get_connection_status
        if not hasattr(self, 'driver') or self.driver is None:
            self.add_log("⚠️ Browser non attivo, inizializzazione...")
            self.driver = get_browser_instance()
            if not get_connection_status():
                self.add_log("❌ Errore: Devi prima connetterti!")
                raise Exception("Errore: Devi prima connetterti!")
            time.sleep(10)  # Attesa più lunga per l'inizializzazione
    
            # Verifica login solo alla prima apertura
            if not check_login(self.driver):
                self.add_log("⚠️ Login necessario")
                return update_ui_and_return("ERRORE: Login necessario", success=False, message="Login necessario")

        # Verifica URL corrente solo se non siamo già in una chat
        current_url = self.driver.current_url
        if "genspark.ai" not in current_url and "/agents" not in current_url and "/chat" not in current_url:
            self.add_log("🔄 Navigazione a Genspark necessaria...")
            self.driver.get("https://genspark.ai")
            time.sleep(10)

        # Usa il nuovo metodo di divisione del prompt
        sections = self.split_prompt(text)

        # DEBUG AGGIUNTIVO - INIZIO
        sections_count = len(sections)
        self.add_log(f"📋 Prompt diviso in {sections_count} sezioni numerate")
        print(f"DEBUG: Prompt diviso in {sections_count} sezioni")
        for i, section in enumerate(sections):
            self.add_log(f"📄 Sezione {i+1}: {section[:50]}..." + ("" if len(section) <= 50 else f" ({len(section)} caratteri)"))
            print(f"DEBUG: Sezione {i+1}: {section[:50].replace(chr(10), ' ')}...")

        # Prendi solo la prima sezione per l'invio corrente
        section_to_send = sections[0] if sections else text

        # Verifica che il browser sia attivo
        from ai_interfaces.browser_manager import get_browser_instance, get_connection_status
        if not hasattr(self, 'driver') or self.driver is None:
            self.add_log("⚠️ Browser non attivo, inizializzazione...")
            self.driver = get_browser_instance()
            if not get_connection_status():
                self.add_log("❌ Errore: Devi prima connetterti!")
                raise Exception("Errore: Devi prima connetterti!")
            time.sleep(10)  # Attesa più lunga per l'inizializzazione

        try:
            # Verifico URL corrente per debugging
            current_url = self.driver.current_url
            self.add_log(f"🌐 URL corrente: {current_url}")
            print(f"DEBUG: URL corrente: {current_url}")

            # Se non siamo in una pagina di chat, naviga a Genspark
            if "genspark.ai" not in current_url:
                self.add_log("🔄 Navigazione a Genspark...")
                self.driver.get("https://genspark.ai")
                time.sleep(10)

            # Massimo 3 tentativi di invio
            max_attempts = 3

            for attempt in range(max_attempts):
                self.add_log(f"🔄 Tentativo {attempt+1}/{max_attempts}")
                print(f"DEBUG: Tentativo di invio {attempt+1}/{max_attempts}")

                try:
                    # 1. PREPARAZIONE: Verifica e pulisci la textarea
                    self.add_log("🧹 Inizio pulizia dell'area di input...")
                    print("DEBUG: Pulizia area input...")
    
                    # Attendi che l'input box sia disponibile con timeout lungo
                    input_box = WebDriverWait(self.driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper textarea"))
                    )
                    print("DEBUG: Input box trovato")
    
                    # Pulizia in più passaggi (metodo intensivo)
                    input_box.clear()
                    time.sleep(1)
    
                    # Ctrl+A e Delete
                    input_box.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    input_box.send_keys(Keys.DELETE)
                    time.sleep(1)
    
                    # Verifica finale con correzione manuale se necessario
                    current_text = input_box.get_attribute("value")
                    if current_text:
                        self.add_log(f"⚠️ Testo residuo: '{current_text}' - pulizia manuale")
                        print(f"DEBUG: Testo residuo dopo pulizia: '{current_text}'")
                        # Metodo manuale: eliminazione carattere per carattere
                        for _ in range(len(current_text) + 5):  # +5 per sicurezza
                            input_box.send_keys(Keys.BACK_SPACE)
                            time.sleep(0.05)
    
                    # Verifica finale
                    final_check = input_box.get_attribute("value")
                    if final_check:
                        self.add_log(f"⚠️ Impossibile pulire completamente: '{final_check}'")
                        print(f"DEBUG: Impossibile pulire completamente: '{final_check}'")
                    else:
                        self.add_log("✅ Area di input completamente pulita")
                        print("DEBUG: Area input pulita con successo")
    
                    # 2. INSERIMENTO TESTO: Carattere per carattere per alta affidabilità
                    self.add_log(f"📝 Inserimento testo carattere per carattere...")
                    print(f"DEBUG: Inserimento testo ({len(section_to_send)} caratteri)...")
    
                    # Metodo 1: Per blocchi di 1-2 caratteri (più lento ma più affidabile)
                    block_size = 2  # Numero di caratteri per blocco
                    for i in range(0, len(section_to_send), block_size):
                        block = section_to_send[i:i+block_size]
                        input_box.send_keys(block)
                        time.sleep(0.01)  # Pausa minima tra blocchi
    
                    # Verifica inserimento
                    time.sleep(2)
                    inserted_text = input_box.get_attribute("value")
                    if not inserted_text:
                        self.add_log("❌ Nessun testo inserito!")
                        print("DEBUG: ERRORE - Nessun testo inserito!")
                        if attempt < max_attempts - 1:
                            continue
                    elif len(inserted_text) < len(section_to_send) * 0.9:
                        self.add_log(f"⚠️ Testo inserito parzialmente: {len(inserted_text)}/{len(section_to_send)} caratteri")
                        print(f"DEBUG: Testo inserito parzialmente: {len(inserted_text)}/{len(section_to_send)} caratteri")
                        if attempt < max_attempts - 1:
                            continue
                    else:
                        self.add_log(f"✅ Testo inserito correttamente: {len(inserted_text)} caratteri")
                        print(f"DEBUG: Testo inserito correttamente: {len(inserted_text)} caratteri")
    
                    # 3. INVIO: Click sul pulsante con metodi multipli
                    self.add_log("🔘 Click sul pulsante di invio...")
                    print("DEBUG: Tentativo click pulsante invio...")
    
                    # Attesa più lunga per il pulsante di invio
                    send_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon"))
                    )
    
                    # Prova entrambi i metodi per maggiore affidabilità
                    try:
                        # Metodo 1: Click standard
                        send_button.click()
                        self.add_log("✅ Click standard eseguito")
                        print("DEBUG: Click standard eseguito")
                    except Exception as click_error:
                        self.add_log(f"⚠️ Errore click standard: {str(click_error)}")
                        print(f"DEBUG: Errore click standard: {str(click_error)}")
        
                        # Metodo 2: Click JavaScript
                        try:
                            self.driver.execute_script("arguments[0].click();", send_button)
                            self.add_log("✅ Click JavaScript eseguito")
                            print("DEBUG: Click JavaScript eseguito")
                        except Exception as js_error:
                            self.add_log(f"❌ Anche click JavaScript fallito: {str(js_error)}")
                            print(f"DEBUG: Anche click JavaScript fallito: {str(js_error)}")
            
                            # Metodo 3: Invio tramite tasto Enter
                            try:
                                input_box.send_keys(Keys.RETURN)
                                self.add_log("✅ Invio tramite tasto Enter")
                                print("DEBUG: Invio tramite tasto Enter")
                            except Exception as enter_error:
                                self.add_log(f"❌ Tutti i metodi di invio falliti: {str(enter_error)}")
                                print(f"DEBUG: Tutti i metodi di invio falliti: {str(enter_error)}")
                                raise Exception("Impossibile inviare il messaggio con nessun metodo")
    
                    # 4. ATTESA RISPOSTA: Sistema di monitoraggio progressivo
                    self.add_log("⏳ Attesa iniziale per la risposta (10 secondi)")
                    print("DEBUG: Attesa iniziale per la risposta (10 secondi)")
                    time.sleep(10)  # Attesa iniziale più lunga

                    # Aggiungi questa riga dopo aver premuto il pulsante di invio e prima del ciclo di attesa
                    debug_response_detection(self.driver)
    
                    # Verifica che la richiesta non sia stata annullata immediatamente
                    try:
                        error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'abortita') or contains(text(), 'aborted')]")
                        if error_elements:
                            self.add_log("❌ Richiesta abortita rilevata immediatamente (BLOCCO 1)")
                            print("DEBUG: Richiesta abortita rilevata immediatamente")
        
                            # AGGIUNGI QUESTO BLOCCO:
                            self.add_log("🧹 Pulisco chat e riprovo lo stesso prompt")
                            from ai_interfaces.browser_manager import clear_chat  # Assicurati che l'import sia corretto
        
                            if clear_chat(self.driver, force_reload=True, maintain_session=True):
                                self.add_log("✅ Chat pulita con successo")
                                if attempt < max_attempts - 1:
                                    time.sleep(10)  # Pausa più lunga prima di riprovare
                                    continue
                                else:
                                    return update_ui_and_return("ERRORE: Richiesta abortita ripetutamente", success=False, message="Richiesta abortita ripetutamente")
                            else:
                                self.add_log("❌ Impossibile pulire la chat")
                                return update_ui_and_return("ERRORE: Impossibile pulire la chat", success=False, message="Impossibile pulire la chat")
        
                            # FINE DEL BLOCCO AGGIUNTO
        
                    except Exception:
                        pass  # Ignora errori nella ricerca di messaggi di errore
    
                    # Ciclo di attesa principale
                    response_complete = False
                    last_length = 0
                    stable_count = 0
                    timeout_cycles = 45  # ~15 minuti totali al massimo (20s per ciclo)
                    message_count = 0
    
                    for cycle in range(timeout_cycles):
                        # Debug del ciclo di attesa
                        print(f"DEBUG: Ciclo di attesa {cycle+1}/{timeout_cycles}")
                    
                        # Cerca di ottenere la risposta con metodi multipli
                        response = None
        
                        # 1. Metodo principale: CSS Selector specifico
                        try:
                            selectors = [
                                ".message-content", 
                                "div.chat-wrapper div.desc > div > div > div",
                                "div.message div.text-wrap",
                                ".chat-message-item .content"
                            ]
            
                            for selector in selectors:
                                try:
                                    messages = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if messages and len(messages) > 0:
                                        # Controlla se c'è un nuovo messaggio o un cambio nel conteggio
                                        if len(messages) > message_count:
                                            message_count = len(messages)
                                            self.add_log(f"📩 Nuovo messaggio rilevato: totale {message_count}")
                                            print(f"DEBUG: Nuovo messaggio rilevato: totale {message_count}")
                        
                                        # Usa l'ultimo messaggio
                                        last_message = messages[-1]
                                        response = last_message.text.strip()
                                        if response:
                                            print(f"DEBUG: Risposta trovata con selettore '{selector}': {len(response)} caratteri")
                                        break
                                except Exception:
                                    continue
                        except Exception as e:
                            self.add_log(f"⚠️ Errore nel recupero risposta: {str(e)}")
                            print(f"DEBUG: Errore nel recupero risposta: {str(e)}")
        
                        # 2. Metodo alternativo: JavaScript diretto
                        if not response:
                            try:
                                js_response = self.driver.execute_script("""
                                    var messages = document.querySelectorAll('.message-content, .chat-message-item, .chat-wrapper .desc');
                                    if (messages && messages.length > 0) {
                                        return messages[messages.length - 1].textContent;
                                    }
                                    return null;
                                """)
                
                                if js_response:
                                    response = js_response.strip()
                                    self.add_log(f"📩 Risposta recuperata via JavaScript: {len(response)} caratteri")
                                    print(f"DEBUG: Risposta recuperata via JavaScript: {len(response)} caratteri")
                            except Exception:
                                pass
        
                        # Se abbiamo ottenuto una risposta, analizzala
                        if response:
                            current_length = len(response)
                        
                            # Debug periodico della risposta in crescita
                            # Cerca di ottenere la risposta con la nuova funzione
                            response = get_ai_response(self.driver)

                            # Se abbiamo ottenuto una risposta, analizzala
                            if response:
                                current_length = len(response)
    
                                # Debug periodico della risposta in crescita
                                if cycle % 5 == 0:  # Ogni 5 cicli
                                    preview = response[:150].replace('\n', ' ')
                                    print(f"DEBUG: Risposta in corso - {current_length} caratteri - Preview: {preview}...")
    
                                # VERIFICA IMPORTANTE: controlla che la risposta NON sia identica alla domanda
                                if response == section_to_send or response == text:
                                    print(f"DEBUG: ATTENZIONE - La risposta è identica alla domanda! Ciclo {cycle+1}")
                                    self.add_log(f"⚠️ Recuperato testo identico alla domanda, non è una risposta valida")
                                    response = None  # Non considerare questa come una risposta valida
        
                                else:
                                    # Controlla gli errori tipici nella risposta
                                    error_indicators = ["richiesta abortita", "request aborted", "troppo lungo", "too long", 
                                                      "errore durante", "error during", "riprova più tardi", "try again later"]
    
                                    if any(indicator in response.lower() for indicator in error_indicators):
                                        self.add_log(f"❌ Errore rilevato nella risposta: {response[:100]}...")
                                        print(f"DEBUG: Errore rilevato nella risposta: {response[:100]}...")
                                        if attempt < max_attempts - 1:
                                            time.sleep(10)
                                            break  # Esci dal ciclo e riprova l'invio
                                        else:
                                            error_msg = f"ERRORE: {response[:200]}"
                                            return update_ui_and_return(error_msg, success=False, message="Errore rilevato nella risposta")
    
                                    # Controlla i terminatori espliciti
                                    if "FINE_RISPOSTA" in response or "FINE" in response:
                                        self.add_log(f"✅ Terminatore esplicito trovato dopo {cycle+1} cicli")
                                        print(f"DEBUG: Terminatore esplicito trovato dopo {cycle+1} cicli")
                                        terminator = "FINE_RISPOSTA" if "FINE_RISPOSTA" in response else "FINE"
                                        terminator_pos = response.find(terminator)
                                        print(f"DEBUG: Terminatore '{terminator}' trovato alla posizione {terminator_pos}")
        
                                        # Pulisci la risposta rimuovendo il terminatore
                                        if "FINE_RISPOSTA" in response:
                                            response = response.split("FINE_RISPOSTA")[0].strip()
                                        elif "FINE" in response:
                                            response = response.split("FINE")[0].strip()
            
                                        return update_ui_and_return(response)
    
                                    # Verifica stabilità della lunghezza
                                    if current_length == last_length and current_length > 50:  # Solo se c'è contenuto significativo
                                        stable_count += 1
                                        self.add_log(f"⏳ Risposta stabile: {stable_count}/5 cicli ({current_length} caratteri)")
                                        print(f"DEBUG: Risposta stabile: {stable_count}/5 cicli ({current_length} caratteri)")
        
                                        if stable_count >= 5:  # 5 cicli di stabilità = risposta completa
                                            self.add_log(f"✅ Risposta stabilizzata dopo {cycle+1} cicli")
                                            print(f"DEBUG: Risposta stabilizzata dopo {cycle+1} cicli")
                                            return update_ui_and_return(response)
                                    else:
                                        stable_count = 0
                                        self.add_log(f"📝 Risposta in evoluzione: {current_length} caratteri (ciclo {cycle+1})")
                                        print(f"DEBUG: Risposta in evoluzione: {current_length} caratteri (ciclo {cycle+1})")
                                        last_length = current_length
                            else:
                                self.add_log(f"⚠️ Nessuna risposta rilevabile al ciclo {cycle+1}")
                                print(f"DEBUG: Nessuna risposta rilevabile al ciclo {cycle+1}")
        
                        # Controlla se abbiamo raggiunto un limite di contesto
                        if cycle % 3 == 0:  # Ogni 3 cicli
                            if self.handle_context_limit():
                                self.add_log("♻️ Limite di contesto rilevato, nuovo tentativo...")
                                print("DEBUG: Limite di contesto rilevato, nuovo tentativo...")
                                return self.send_to_genspark(section_to_send)
        
                        # Attendi prima del prossimo ciclo
                        time.sleep(20)  # 20 secondi tra i cicli
    
                    # Se siamo qui, il timeout è scaduto
                    if response:
                        self.add_log(f"⚠️ Timeout ma risposta parziale disponibile: {len(response)} caratteri")
                        print(f"DEBUG: Timeout ma risposta parziale disponibile: {len(response)} caratteri")
                        print(f"DEBUG: Salvataggio risposta parziale - Lunghezza: {len(response)}")
                        print(f"DEBUG: Preview risposta parziale: {response[:200].replace(chr(10), ' ')}...")
                        return update_ui_and_return(response, message="Timeout, risposta parziale")
                    else:
                        self.add_log("❌ Timeout senza risposta")
                        print("DEBUG: Timeout senza risposta")
        
                        if attempt < max_attempts - 1:
                            retry_delay = 15 * (attempt + 1)  # Aumenta il ritardo ad ogni tentativo
                            self.add_log(f"🔄 Tentativo {attempt+2} dopo timeout - attesa {retry_delay} secondi")
                            print(f"DEBUG: Tentativo {attempt+2} dopo timeout - attesa {retry_delay} secondi")
                            time.sleep(retry_delay)
                        else:
                            error_msg = "TIMEOUT: Nessuna risposta ricevuta dopo ripetuti tentativi"
                            return update_ui_and_return(error_msg, success=False, message="Timeout senza risposta")
    
                except Exception as e:
                    # Gestione errori specifici per sezione
                    self.add_log(f"⚠️ Errore sezione, tentativo {attempt+1}: {str(e)}")
                    print(f"DEBUG: Errore sezione, tentativo {attempt+1}: {str(e)}")
                
                    # Cattura screenshot per debug
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        screenshot_path = f"error_section_try_{attempt+1}_{timestamp}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.add_log(f"📸 Screenshot: {screenshot_path}")
                        print(f"DEBUG: Screenshot errore: {screenshot_path}")
                    except Exception:
                        pass
                
                    if attempt < max_attempts - 1:
                        attempt_delay = 15 * (attempt + 1)
                        print(f"DEBUG: Attesa {attempt_delay}s prima del prossimo tentativo...")
                        time.sleep(attempt_delay)
                    else:
                        self.add_log("❌ Tutti i tentativi falliti")
                        print("DEBUG: Tutti i tentativi falliti")
                        error_msg = f"ERRORE: {str(e)}"
                        return update_ui_and_return(error_msg, success=False, message=str(e))

            # Se arriviamo qui, tutti i tentativi sono falliti
            error_msg = "ERRORE: Tutti i tentativi falliti con errori diversi"
            print("DEBUG: Tutti i tentativi falliti con errori diversi")
            return update_ui_and_return(error_msg, success=False, message="Errori multipli")

        except Exception as e:
            # Errore globale
            error_message = f"ERRORE CRITICO: {str(e)}"
            self.add_log(f"❌ {error_message}")
            print(f"DEBUG: ERRORE CRITICO: {str(e)}")
        
            import traceback
            error_trace = traceback.format_exc()
            print(f"DEBUG: Traceback completo:\n{error_trace}")

            # Cattura screenshot finale
            try:
                screenshot_path = f"critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                self.add_log(f"📸 Screenshot errore critico: {screenshot_path}")
                print(f"DEBUG: Screenshot errore critico: {screenshot_path}")
            except Exception:
                pass
    
            return update_ui_and_return(error_message, success=False, message=str(e))

        # Log iniziale con stack trace per debugging
        import traceback
        call_stack = traceback.format_stack()
        stack_info = "\n".join(call_stack[-5:])

        self.add_log(f"🔍 [{location}] Inizio invio prompt")
        self.add_log(f"🔍 Inizio invio prompt ({len(text)} caratteri) in {location}")

        # Verifica che il browser sia attivo
        from ai_interfaces.browser_manager import get_browser_instance, get_connection_status
        if not hasattr(self, 'driver') or self.driver is None:
            self.add_log("⚠️ Browser non attivo, inizializzazione...")
            self.driver = get_browser_instance()
            if not get_connection_status():
                self.add_log("❌ Errore: Devi prima connetterti!")
                raise Exception("Errore: Devi prima connetterti!")
            time.sleep(10)  # Attesa più lunga per l'inizializzazione
    
            # Verifica login solo alla prima apertura
            if not check_login(self.driver):
                self.add_log("⚠️ Login necessario")
                return update_ui_and_return("ERRORE: Login necessario", success=False, message="Login necessario")

        # Verifica URL corrente solo se non siamo già in una chat
        current_url = self.driver.current_url
        if "genspark.ai" not in current_url and "/agents" not in current_url and "/chat" not in current_url:
            self.add_log("🔄 Navigazione a Genspark necessaria...")
            self.driver.get("https://genspark.ai")
            time.sleep(10)

        # Usa il nuovo metodo di divisione del prompt
        sections = self.split_prompt(text)

        # DEBUG AGGIUNTIVO - INIZIO
        sections_count = len(sections)
        self.add_log(f"DEBUG_DECISIVO: Testo diviso in {sections_count} sezioni")
        for i, section in enumerate(sections):
            self.add_log(f"DEBUG_DECISIVO: Sezione {i+1} inizia con: {section[:50]}...")

        # Prendi solo la prima sezione per l'invio corrente
        section_to_send = sections[0] if sections else text

        # DEBUG AGGIUNTIVO - FINE
        print(f"DEBUG_DECISIVO: Testo originale contiene {sections_count} sezioni numerate")
        print(f"DEBUG_DECISIVO: Sezioni presenti: 1.={'1.' in text}, 2.={'2.' in text}, 3.={'3.' in text}, 4.={'4.' in text}, 5.={'5.' in text}")
        print(f"DEBUG_DECISIVO: Invio sezione: {section_to_send[:200]}...")

        # Verifica che il browser sia attivo
        from ai_interfaces.browser_manager import get_browser_instance, get_connection_status
        if not hasattr(self, 'driver') or self.driver is None:
            self.add_log("⚠️ Browser non attivo, inizializzazione...")
            self.driver = get_browser_instance()
            if not get_connection_status():
                self.add_log("❌ Errore: Devi prima connetterti!")
                raise Exception("Errore: Devi prima connetterti!")
            time.sleep(10)  # Attesa più lunga per l'inizializzazione

        try:
            # Verifico URL corrente per debugging
            current_url = self.driver.current_url
            self.add_log(f"🌐 URL corrente: {current_url}")

            # Se non siamo in una pagina di chat, naviga a Genspark
            if "genspark.ai" not in current_url:
                self.add_log("🔄 Navigazione a Genspark...")
                self.driver.get("https://genspark.ai")
                time.sleep(10)

            # Massimo 3 tentativi di invio
            max_attempts = 3

            for attempt in range(max_attempts):
                self.add_log(f"🔄 Tentativo {attempt+1}/{max_attempts}")
    
                try:
                    # 1. PREPARAZIONE: Verifica e pulisci la textarea
                    self.add_log("🧹 Inizio pulizia dell'area di input...")
        
                    # Attendi che l'input box sia disponibile con timeout lungo
                    input_box = WebDriverWait(self.driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper textarea"))
                    )
        
                    # Pulizia in più passaggi (metodo intensivo)
                    input_box.clear()
                    time.sleep(1)
        
                    # Ctrl+A e Delete
                    input_box.send_keys(Keys.CONTROL + "a")
                    time.sleep(0.5)
                    input_box.send_keys(Keys.DELETE)
                    time.sleep(1)
        
                    # Verifica finale con correzione manuale se necessario
                    current_text = input_box.get_attribute("value")
                    if current_text:
                        self.add_log(f"⚠️ Testo residuo: '{current_text}' - pulizia manuale")
                        # Metodo manuale: eliminazione carattere per carattere
                        for _ in range(len(current_text) + 5):  # +5 per sicurezza
                            input_box.send_keys(Keys.BACK_SPACE)
                            time.sleep(0.05)
        
                    # Verifica finale
                    final_check = input_box.get_attribute("value")
                    if final_check:
                        self.add_log(f"⚠️ Impossibile pulire completamente: '{final_check}'")
                    else:
                        self.add_log("✅ Area di input completamente pulita")
        
                    # 2. INSERIMENTO TESTO: Carattere per carattere per alta affidabilità
                    self.add_log(f"📝 Inserimento testo carattere per carattere...")
        
                    # Metodo 1: Per blocchi di 1-2 caratteri (più lento ma più affidabile)
                    block_size = 2  # Numero di caratteri per blocco
                    for i in range(0, len(section_to_send), block_size):
                        block = section_to_send[i:i+block_size]
                        input_box.send_keys(block)
                        time.sleep(0.01)  # Pausa minima tra blocchi
        
                    # Verifica inserimento
                    time.sleep(2)
                    inserted_text = input_box.get_attribute("value")
                    if not inserted_text:
                        self.add_log("❌ Nessun testo inserito!")
                        if attempt < max_attempts - 1:
                            continue
                    elif len(inserted_text) < len(section_to_send) * 0.9:
                        self.add_log(f"⚠️ Testo inserito parzialmente: {len(inserted_text)}/{len(section_to_send)} caratteri")
                        if attempt < max_attempts - 1:
                            continue
                    else:
                        self.add_log(f"✅ Testo inserito correttamente: {len(inserted_text)} caratteri")
        
                    # 3. INVIO: Click sul pulsante con metodi multipli
                    self.add_log("🔘 Click sul pulsante di invio...")
        
                    # Attesa più lunga per il pulsante di invio
                    send_button = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon"))
                    )
        
                    # Prova entrambi i metodi per maggiore affidabilità
                    try:
                        # Metodo 1: Click standard
                        send_button.click()
                        self.add_log("✅ Click standard eseguito")
                    except Exception as click_error:
                        self.add_log(f"⚠️ Errore click standard: {str(click_error)}")
            
                        # Metodo 2: Click JavaScript
                        try:
                            self.driver.execute_script("arguments[0].click();", send_button)
                            self.add_log("✅ Click JavaScript eseguito")
                        except Exception as js_error:
                            self.add_log(f"❌ Anche click JavaScript fallito: {str(js_error)}")
                
                            # Metodo 3: Invio tramite tasto Enter
                            try:
                                input_box.send_keys(Keys.RETURN)
                                self.add_log("✅ Invio tramite tasto Enter")
                            except Exception as enter_error:
                                self.add_log(f"❌ Tutti i metodi di invio falliti: {str(enter_error)}")
                                raise Exception("Impossibile inviare il messaggio con nessun metodo")
        
                    # 4. ATTESA RISPOSTA: Sistema di monitoraggio progressivo
                    self.add_log("⏳ Attesa iniziale per la risposta (10 secondi)")
                    time.sleep(10)  # Attesa iniziale più lunga
        
                    # Verifica che la richiesta non sia stata annullata immediatamente
                    try:
                        error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'abortita') or contains(text(), 'aborted')]")
                        if error_elements:
                            self.add_log("❌ Richiesta abortita rilevata immediatamente (BLOCCO 2)")
        
                            # AGGIUNGI QUESTO BLOCCO:
                            self.add_log("🧹 Pulisco chat e riprovo lo stesso prompt")
                            from ai_interfaces.browser_manager import clear_chat  # Assicurati che l'import sia corretto
        
                            if clear_chat(self.driver, force_reload=True, maintain_session=True):
                                self.add_log("✅ Chat pulita con successo")
                                if attempt < max_attempts - 1:
                                    time.sleep(10)  # Pausa più lunga prima di riprovare
                                    continue
                                else:
                                    return update_ui_and_return("ERRORE: Richiesta abortita ripetutamente", success=False, message="Richiesta abortita ripetutamente")
                            else:
                                self.add_log("❌ Impossibile pulire la chat")
                                return update_ui_and_return("ERRORE: Impossibile pulire la chat", success=False, message="Impossibile pulire la chat")
        
                            # FINE DEL BLOCCO AGGIUNTO
        
                    except Exception:
                        pass  # Ignora errori nella ricerca di messaggi di errore
        
                    # Ciclo di attesa principale
                    response_complete = False
                    last_length = 0
                    stable_count = 0
                    timeout_cycles = 45  # ~15 minuti totali al massimo (20s per ciclo)
                    message_count = 0
        
                    for cycle in range(timeout_cycles):
                        # Cerca di ottenere la risposta con metodi multipli
                        response = None
            
                        # 1. Metodo principale: CSS Selector specifico
                        try:
                            selectors = [
                                ".message-content", 
                                "div.chat-wrapper div.desc > div > div > div",
                                "div.message div.text-wrap",
                                ".chat-message-item .content"
                            ]
                
                            for selector in selectors:
                                try:
                                    messages = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                    if messages and len(messages) > 0:
                                        # Controlla se c'è un nuovo messaggio o un cambio nel conteggio
                                        if len(messages) > message_count:
                                            message_count = len(messages)
                                            self.add_log(f"📩 Nuovo messaggio rilevato: totale {message_count}")
                            
                                        # Usa l'ultimo messaggio
                                        last_message = messages[-1]
                                        response = last_message.text.strip()
                                        break
                                except Exception:
                                    continue
                        except Exception as e:
                            self.add_log(f"⚠️ Errore nel recupero risposta: {str(e)}")
            
                        # 2. Metodo alternativo: JavaScript diretto
                        if not response:
                            try:
                                js_response = self.driver.execute_script("""
                                    var messages = document.querySelectorAll('.message-content, .chat-message-item, .chat-wrapper .desc');
                                    if (messages && messages.length > 0) {
                                        return messages[messages.length - 1].textContent;
                                    }
                                    return null;
                                """)
                    
                                if js_response:
                                    response = js_response.strip()
                                    self.add_log(f"📩 Risposta recuperata via JavaScript: {len(response)} caratteri")
                            except Exception:
                                pass
            
                        # Se abbiamo ottenuto una risposta, analizzala
                        if response:
                            current_length = len(response)
                
                            # Controlla gli errori tipici nella risposta
                            error_indicators = ["richiesta abortita", "request aborted", "troppo lungo", "too long", 
                                               "errore durante", "error during", "riprova più tardi", "try again later"]
                
                            if any(indicator in response.lower() for indicator in error_indicators):
                                self.add_log(f"❌ Errore rilevato nella risposta: {response[:100]}...")
                                if attempt < max_attempts - 1:
                                    time.sleep(10)
                                    break  # Esci dal ciclo e riprova l'invio
                                else:
                                    error_msg = f"ERRORE: {response[:200]}"
                                    return update_ui_and_return(error_msg, success=False, message="Errore rilevato nella risposta")
                
                            # Controlla i terminatori espliciti
                            if "FINE_RISPOSTA" in response or "FINE" in response:
                                self.add_log(f"✅ Terminatore esplicito trovato dopo {cycle+1} cicli")
                    
                                # Pulisci la risposta rimuovendo il terminatore
                                if "FINE_RISPOSTA" in response:
                                    response = response.split("FINE_RISPOSTA")[0].strip()
                                elif "FINE" in response:
                                    response = response.split("FINE")[0].strip()
                        
                                return update_ui_and_return(response)
                
                            # Verifica stabilità della lunghezza
                            if current_length == last_length:
                                stable_count += 1
                                self.add_log(f"⏳ Risposta stabile: {stable_count}/5 cicli ({current_length} caratteri)")
                    
                                if stable_count >= 5:  # 5 cicli di stabilità = risposta completa
                                    self.add_log(f"✅ Risposta stabilizzata dopo {cycle+1} cicli")
                                    return update_ui_and_return(response)
                            else:
                                stable_count = 0
                                self.add_log(f"📝 Risposta in evoluzione: {current_length} caratteri (ciclo {cycle+1})")
                                last_length = current_length
                        else:
                            self.add_log(f"⚠️ Nessuna risposta rilevabile al ciclo {cycle+1}")
            
                        # Controlla se abbiamo raggiunto un limite di contesto
                        if cycle % 3 == 0:  # Ogni 3 cicli
                            if self.handle_context_limit():
                                self.add_log("♻️ Limite di contesto rilevato, nuovo tentativo...")
                                return self.send_to_genspark(section_to_send)
            
                        # Attendi prima del prossimo ciclo
                        time.sleep(20)  # 20 secondi tra i cicli
        
                    # Se siamo qui, il timeout è scaduto
                    if response:
                        self.add_log(f"⚠️ Timeout ma risposta parziale disponibile: {len(response)} caratteri")
                        return update_ui_and_return(response, message="Timeout, risposta parziale")
                    else:
                        self.add_log("❌ Timeout senza risposta")
            
                        if attempt < max_attempts - 1:
                            retry_delay = 15 * (attempt + 1)  # Aumenta il ritardo ad ogni tentativo
                            self.add_log(f"🔄 Tentativo {attempt+2} dopo timeout - attesa {retry_delay} secondi")
                            time.sleep(retry_delay)
                        else:
                            error_msg = "TIMEOUT: Nessuna risposta ricevuta dopo ripetuti tentativi"
                            return update_ui_and_return(error_msg, success=False, message="Timeout senza risposta")
        
                except Exception as e:
                    self.add_log(f"❌ Errore durante tentativo {attempt+1}: {str(e)}")
        
                    # Cattura screenshot per diagnosi
                    try:
                        screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        self.driver.save_screenshot(screenshot_path)
                        self.add_log(f"📸 Screenshot errore: {screenshot_path}")
                    except Exception:
                        pass
        
                    if attempt < max_attempts - 1:
                        self.add_log(f"🔄 Attesa 20 secondi prima del tentativo {attempt+2}...")
                        time.sleep(20)
                    else:
                        self.add_log("❌ Tutti i tentativi falliti")
                        error_msg = f"ERRORE: {str(e)}"
                        return update_ui_and_return(error_msg, success=False, message=str(e))

            # Se arriviamo qui, tutti i tentativi sono falliti
            error_msg = "ERRORE: Tutti i tentativi falliti con errori diversi"
            return update_ui_and_return(error_msg, success=False, message="Errori multipli")

        except Exception as e:
            # Errore globale
            error_message = f"ERRORE CRITICO: {str(e)}"
            self.add_log(f"❌ {error_message}")
            logging.error(f"Errore in send_to_genspark: {str(e)}\n{traceback.format_exc()}")

            # Cattura screenshot finale
            try:
                screenshot_path = f"critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.driver.save_screenshot(screenshot_path)
                self.add_log(f"📸 Screenshot errore critico: {screenshot_path}")
            except Exception:
                pass
        
            return update_ui_and_return(error_message, success=False, message=str(e))

def debug_response_detection(driver):
    """
    Funzione diagnostica per testare tutti i possibili metodi di recupero risposta.
    Utile per identificare quale selettore funziona meglio con l'interfaccia attuale.
    
    Chiamare questa funzione dopo l'invio di un prompt e attendere la risposta.
    """
    print("\n===== DIAGNOSTICA RISPOSTA AI =====")
    
    # Salva la pagina HTML per analisi offline
    try:
        html = driver.execute_script("return document.documentElement.outerHTML")
        with open("debug_genspark_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✓ HTML della pagina salvato in debug_genspark_page.html")
    except Exception as e:
        print(f"✗ Errore nel salvataggio HTML: {e}")
    
    # Testa tutti i possibili selettori
    selectors_to_test = [
        "div.agent-turn div.message",
        "div[data-message-author-role='assistant']", 
        "div.message.agent, div.message.bot",
        "div.chat-wrapper div.message:nth-child(even)",
        "div.message div.text-wrap",
        ".message-content",
        "div.chat-wrapper div.desc > div > div > div"
    ]
    
    print("\nTest selettori CSS:")
    for selector in selectors_to_test:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"\nSelettore: '{selector}'")
            print(f"- Elementi trovati: {len(elements)}")
            
            if elements:
                for i, el in enumerate(elements[-2:]):  # Mostra solo gli ultimi 2 elementi
                    text = el.text.strip()
                    print(f"- Elemento {len(elements)-1-i}: {len(text)} caratteri")
                    print(f"  Anteprima: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
        except Exception as e:
            print(f"- Errore: {e}")
    
    # Testa JavaScript
    try:
        js_output = driver.execute_script("""
            return {
                messageCount: document.querySelectorAll('.message, .chat-message-item').length,
                lastMessage: (document.querySelectorAll('.message, .chat-message-item').length > 0) ? 
                    document.querySelectorAll('.message, .chat-message-item')[document.querySelectorAll('.message, .chat-message-item').length - 1].textContent.substring(0, 100) : 
                    'nessun messaggio trovato',
                responseCount: document.querySelectorAll('.agent-turn, [data-message-author-role="assistant"]').length
            }
        """)
        print("\nJS Diagnostica:")
        print(f"- Totale messaggi: {js_output['messageCount']}")
        print(f"- Risposte AI rilevate: {js_output['responseCount']}")
        print(f"- Ultimo messaggio: \"{js_output['lastMessage']}\"")
    except Exception as e:
        print(f"- Errore JavaScript: {e}")
    
    print("\n- Test risposta con get_ai_response(): ", end="")
    try:
        response = get_ai_response(driver)
        if response:
            print(f"trovati {len(response)} caratteri")
            print(f"  Anteprima: \"{response[:100]}{'...' if len(response) > 100 else ''}\"")
        else:
            print("nessuna risposta trovata")
    except Exception as e:
        print(f"errore: {e}")
    
    print("===================================\n")

def get_clean_input_box(driver, log_callback=None):
    """
    Ottiene e pulisce completamente la casella di input
    
    Args:
        driver: WebDriver di Selenium
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        WebElement: Elemento input box pulito o None in caso di errore
    """
    # Importazioni necessarie
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Funzione di logging
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        # Attesa lunga per l'input box
        input_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper textarea"))
        )
    
        # Pulizia in tre passaggi
        # 1. Clear standard
        input_box.clear()
        time.sleep(1)
    
        # 2. Ctrl+A e Delete
        input_box.send_keys(Keys.CONTROL + "a")
        time.sleep(0.5)
        input_box.send_keys(Keys.DELETE)
        time.sleep(1)
    
        # 3. Verifica finale e correzione
        current_text = input_box.get_attribute("value")
        if current_text:
            # Click e backspace multipli
            input_box.click()
            for _ in range(len(current_text) + 10):
                input_box.send_keys(Keys.BACK_SPACE)
                time.sleep(0.05)
    
        return input_box
    except Exception as e:
        if log_callback:
            log_callback(f"⚠️ Errore nella pulizia dell'input box: {str(e)}")
        print(f"ERROR - Eccezione in get_clean_input_box: {str(e)}")
        return None

def safe_text_input(driver, input_box, text, log_callback=None):
    """
    Inserisce il testo in modo sicuro nella casella di input
    
    Args:
        driver: WebDriver di Selenium
        input_box: Elemento input box WebElement
        text: Testo da inserire
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        None
    """
    import time
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    if len(text) < 200:
        # Per testi brevi, inserisci tutto insieme
        input_box.send_keys(text)
        time.sleep(1)
    else:
        # Per testi lunghi, inserisci a blocchi di caratteri
        for i in range(0, len(text), 50):
            chunk = text[i:i+50]
            input_box.send_keys(chunk)
            time.sleep(0.1)

    # Breve pausa finale dopo inserimento
    time.sleep(1)

def click_send_button(driver, log_callback=None):
    """
    Tenta di cliccare il pulsante di invio con metodi multipli
    
    Args:
        driver: WebDriver di Selenium
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        bool: True se il click è riuscito, False altrimenti
    """
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        # Metodo 1: Click standard
        send_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon"))
        )
        send_button.click()
        time.sleep(1)
        return True
    except Exception:
        try:
            # Metodo 2: Click JavaScript
            send_button = driver.find_element(By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon")
            driver.execute_script("arguments[0].click();", send_button)
            time.sleep(1)
            return True
        except Exception:
            try:
                # Metodo 3: Tasto invio nella textarea
                textarea = driver.find_element(By.CSS_SELECTOR, "div.search-input-wrapper textarea")
                textarea.send_keys(Keys.RETURN)
                time.sleep(1)
                return True
            except Exception:
                return False

def wait_for_stable_response(driver, max_wait_cycles=45, stability_threshold=10, cycle_wait=20, log_callback=None):
    """
    Sistema avanzato di attesa per risposta stabile
    
    Args:
        driver: WebDriver di Selenium
        max_wait_cycles: Numero massimo di cicli di attesa
        stability_threshold: Numero di cicli stabili necessari
        cycle_wait: Tempo di attesa tra i cicli in secondi
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        tuple: (testo risposta, flag successo)
    """
    import time
    from selenium.webdriver.common.by import By
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    # Importare handle_context_limit dopo averla definita per evitare import circolari
    from ai_interfaces.browser_manager import handle_context_limit
            
    log(f"⏳ Inizio attesa risposta (max {max_wait_cycles} cicli)")

    # Inizializzazione variabili di monitoraggio
    last_length = 0
    stable_count = 0
    response_text = None

    for cycle in range(max_wait_cycles):
        try:
            # Verifica limite contesto ogni 3 cicli
            if cycle % 3 == 0 and handle_context_limit(driver, log_callback):
                log("♻️ Limite contesto gestito durante attesa")
                # Riprovare da capo se c'è stato reset? Per ora continuiamo
        
            # Prova diversi selettori per le risposte
            selectors = [
                ".message-content", 
                "div.chat-wrapper div.desc > div > div > div",
                "div.message div.text-wrap",
                ".chat-message-item .content"
            ]
        
            # Cerca la risposta con tutti i selettori
            for selector in selectors:
                try:
                    messages = driver.find_elements(By.CSS_SELECTOR, selector)
                    if messages and len(messages) > 0:
                        current_text = messages[-1].text.strip()
                        if current_text:
                            response_text = current_text
                        
                            # Verifica terminazione esplicita
                            if "FINE_RISPOSTA" in response_text or "FINE" in response_text:
                                log(f"✅ Terminatore esplicito trovato al ciclo {cycle+1}")
                                return response_text, True
                        
                            # Verifica errori tipici
                            error_indicators = ["richiesta abortita", "request aborted", 
                                               "troppo lungo", "too long", 
                                               "errore durante", "error during"]
                        
                            if any(e in response_text.lower() for e in error_indicators):
                                log(f"❌ Errore rilevato nella risposta al ciclo {cycle+1}")
                                return response_text, False
                        
                            # Verifica stabilità
                            current_length = len(response_text)
                            if current_length == last_length:
                                stable_count += 1
                                log(f"⏳ Risposta stabile: {stable_count}/{stability_threshold} cicli ({current_length} caratteri)")
                            
                                if stable_count >= stability_threshold:
                                    log(f"✅ Risposta completata dopo {cycle+1} cicli")
                                    return response_text, True
                            else:
                                stable_count = 0
                                log(f"📝 Risposta in evoluzione: {current_length} caratteri (ciclo {cycle+1})")
                                last_length = current_length
                        
                            # Trovata risposta valida, esci dal ciclo selettori
                            break
                except Exception:
                    continue
        
            # Attendi prima del prossimo ciclo
            time.sleep(cycle_wait)
    
        except Exception as e:
            log(f"⚠️ Errore durante attesa risposta: {str(e)}")
            time.sleep(cycle_wait)

    # Timeout raggiunto
    log(f"⏱️ Timeout dopo {max_wait_cycles} cicli di attesa")
    return response_text, False


def split_prompt(text, prompt_id=None, section_number=None, log_callback=None):
    """
    Divide il prompt in sezioni numeriche mantenendo l'integrità.
    Aggiunto tracciamento della posizione nel flusso.
    
    Args:
        text: Testo del prompt da dividere
        prompt_id: ID del prompt (opzionale)
        section_number: Numero della sezione (opzionale)
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        list: Lista di sezioni del prompt
    """
    import re
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    # Log della posizione corrente
    location = f"Prompt {section_number if section_number else 'unknown'} di {prompt_id if prompt_id else 'unknown'}"
    log(f"DEBUG_LOCATION: Analisi in {location}")

    # Prima pulizia: rimuovi eventuali risposte precedenti
    if "PROMPT ------" in text:
        text = text.split("PROMPT ------")[1].split("------ END PROMPT")[0].strip()
        log(f"DEBUG_CLEAN: Estratto contenuto prompt pulito in {location}")

    sections = []
    # Usa regex per trovare sezioni che iniziano con numero e punto
    section_matches = re.finditer(r'(?:^|\n)\s*(\d+)\.\s+(.*?)(?=(?:\n\s*\d+\.|$))', text, re.DOTALL)

    for match in section_matches:
        section_num = match.group(1)
        section_content = match.group(2).strip()
        if section_content:
            sections.append(f"{section_num}. {section_content}")
            log(f"DEBUG_SECTION: Trovata sezione {section_num} in {location}")
            log(f"DEBUG_CONTENT: Primi 100 caratteri: {section_content[:100]}...")

    # Se non trova sezioni numerate, restituisci il testo intero
    if not sections:
        log(f"DEBUG_WARNING: Nessuna sezione numerata trovata in {location}")
        return [text]
    
    log(f"DEBUG_SUMMARY: Trovate {len(sections)} sezioni numerate valide in {location}")

    # Verifica contenuto per possibili errori
    for i, section in enumerate(sections):
        if "BSR medio" in section or "Competitività:" in section:
            log(f"DEBUG_ERROR: Possibile contenuto di risposta trovato nella sezione {i+1} di {location}")
            log(f"DEBUG_CONTENT_ERROR: {section[:200]}...")

    return sections