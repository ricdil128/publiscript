"""
Driver principale per interazione con Genspark.
Gestisce la connessione e l'invio di prompt.
"""
import re
import time
import os
import logging
import traceback
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importazioni interne
from ai_interfaces.browser_manager import setup_browser, check_login, handle_context_limit, create_fresh_chat
from ai_interfaces.interaction_utils import clear_chat, split_prompt
from .file_text_utils import clean_text, split_text

# ============================================================
# FUNZIONI DI INTERAZIONE CON GENSPARK
# ============================================================

def send_to_genspark(driver, text, log_callback=None, prompt_id=None, section_number=None, cooldown_manager=None, chat_manager=None, results_display=None):
    """
    Invia un messaggio a Genspark e attende la risposta.
    Versione completamente rivista per garantire stabilità e affidabilità,
    con aggiornamento dell'interfaccia utente integrato.
    
    Args:
        driver: WebDriver di Selenium
        text: Testo da inviare
        log_callback: Funzione per loggare messaggi
        prompt_id: ID del prompt (opzionale)
        section_number: Numero della sezione (opzionale)
        cooldown_manager: Gestore dei cooldown (opzionale)
        chat_manager: Gestore delle chat (opzionale)
        results_display: Elemento UI per visualizzare i risultati (opzionale)
        
    Returns:
        str: Risposta di Genspark
    """
    # Funzione di logging interna
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    # Funzione di supporto per loggare la posizione nel prompt
    def log_prompt_location(prompt_id, section_number, action):
        location = f"{prompt_id}_{section_number}"
        log(f"[{location}] {action}")
        return location
        
    # Aggiungi informazioni sul numero della domanda/prompt
    question_number = None
    if text and text.strip():
        # Cerca un pattern come "1)" o "2." all'inizio del testo
        match = re.match(r'^\s*(\d+)[\.|\)]', text)
        if match:
            question_number = match.group(1)
            log(f"⚙️ Elaborazione domanda #{question_number}")

    if cooldown_manager:
        cooldown_manager.track_request()

    # Log iniziale con posizione nel flusso
    location = log_prompt_location(
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
            if chat_manager:
                print(f"DEBUG: Chiamata a chat_manager.save_response per {location}")
                metadata = {
                    "prompt_id": prompt_id,
                    "section_number": section_number,
                    "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S'),
                    "has_terminator": has_end
                }
                # Verifica se il file di contesto esiste prima di salvare
                context_file = getattr(chat_manager, 'context_file', 'context.txt')
                print(f"DEBUG: Verifica file context.txt - Esiste: {os.path.exists(context_file)}")
            
                # Salva la risposta
                try:
                    chat_manager.save_response(response, f"Prompt {prompt_id}-{section_number}", metadata)
                    print(f"DEBUG: Risposta salvata con successo in {context_file}")
                except Exception as save_error:
                    print(f"DEBUG: ERRORE durante il salvataggio della risposta: {str(save_error)}")
                    print(f"DEBUG: Traceback salvataggio:\n{traceback.format_exc()}")
        else:
            print("DEBUG: Risposta vuota o None")
        
        if results_display and response:
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
        
                results_display.update(value=html_response)
                log(f"✅ Interfaccia aggiornata con risposta di {len(response)} caratteri")
                print(f"DEBUG: UI aggiornata con risposta di {len(response)} caratteri")
            except Exception as ui_error:
                log(f"❌ Errore nell'aggiornamento dell'interfaccia: {str(ui_error)}")
                print(f"DEBUG: Errore nell'aggiornamento UI: {str(ui_error)}")

        return response

    # Log iniziale con stack trace per debugging
    call_stack = traceback.format_stack()
    stack_info = "\n".join(call_stack[-5:])

    log(f"🔍 [{location}] Inizio invio prompt")
    log(f"🔍 Inizio invio prompt ({len(text)} caratteri) in {location}")

    # Verifica che il browser sia attivo
    if driver is None:
        log("⚠️ Browser non attivo, inizializzazione...")
        driver = get_browser_instance()
        driver.get("https://genspark.ai")
        time.sleep(10)  # Attesa più lunga per l'inizializzazione
    
        # Verifica login solo alla prima apertura
        if not check_login(driver):
            log("⚠️ Login necessario")
            return update_ui_and_return("ERRORE: Login necessario", success=False, message="Login necessario")

    # Verifica URL corrente solo se non siamo già in una chat
    current_url = driver.current_url
    if "genspark.ai" not in current_url and "/agents" not in current_url and "/chat" not in current_url:
        log("🔄 Navigazione a Genspark necessaria...")
        driver.get("https://genspark.ai")
        time.sleep(10)

    # Usa il metodo di divisione del prompt
    sections = split_prompt(text, prompt_id, section_number)

    # DEBUG AGGIUNTIVO - INIZIO
    sections_count = len(sections)
    log(f"📋 Prompt diviso in {sections_count} sezioni numerate")
    print(f"DEBUG: Prompt diviso in {sections_count} sezioni")
    for i, section in enumerate(sections):
        log(f"📄 Sezione {i+1}: {section[:50]}..." + ("" if len(section) <= 50 else f" ({len(section)} caratteri)"))
        print(f"DEBUG: Sezione {i+1}: {section[:50].replace(chr(10), ' ')}...")

    # Prendi solo la prima sezione per l'invio corrente
    section_to_send = sections[0] if sections else text

    # Verifica che il browser sia attivo
    if driver is None:
        log("⚠️ Browser non attivo, inizializzazione...")
        driver = get_browser_instance()
        driver.get("https://genspark.ai")
        time.sleep(10)  # Attesa più lunga per l'inizializzazione

    try:
        # Verifico URL corrente per debugging
        current_url = driver.current_url
        log(f"🌐 URL corrente: {current_url}")
        print(f"DEBUG: URL corrente: {current_url}")

        # Se non siamo in una pagina di chat, naviga a Genspark
        if "genspark.ai" not in current_url:
            log("🔄 Navigazione a Genspark...")
            driver.get("https://genspark.ai")
            time.sleep(10)

        # Massimo tentativi di invio
        max_attempts = 5

        for attempt in range(max_attempts):
            log(f"🔄 Tentativo {attempt+1}/{max_attempts}")
            print(f"DEBUG: Tentativo di invio {attempt+1}/{max_attempts}")

            try:
                # 1. PREPARAZIONE: Verifica e pulisci la textarea
                log("🧹 Inizio pulizia dell'area di input...")
                print("DEBUG: Pulizia area input...")

                # Attendi che l'input box sia disponibile con timeout lungo
                input_box = WebDriverWait(driver, 20).until(
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
                    log(f"⚠️ Testo residuo: '{current_text}' - pulizia manuale")
                    print(f"DEBUG: Testo residuo dopo pulizia: '{current_text}'")
                    # Metodo manuale: eliminazione carattere per carattere
                    for _ in range(len(current_text) + 5):  # +5 per sicurezza
                        input_box.send_keys(Keys.BACK_SPACE)
                        time.sleep(0.05)

                # Verifica finale
                final_check = input_box.get_attribute("value")
                if final_check:
                    log(f"⚠️ Impossibile pulire completamente: '{final_check}'")
                    print(f"DEBUG: Impossibile pulire completamente: '{final_check}'")
                else:
                    log("✅ Area di input completamente pulita")
                    print("DEBUG: Area input pulita con successo")

                # 2. INSERIMENTO TESTO: Carattere per carattere per alta affidabilità
                log(f"📝 Inserimento testo carattere per carattere...")
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
                    log("❌ Nessun testo inserito!")
                    print("DEBUG: ERRORE - Nessun testo inserito!")
                    if attempt < max_attempts - 1:
                        continue
                elif len(inserted_text) < len(section_to_send) * 0.9:
                    log(f"⚠️ Testo inserito parzialmente: {len(inserted_text)}/{len(section_to_send)} caratteri")
                    print(f"DEBUG: Testo inserito parzialmente: {len(inserted_text)}/{len(section_to_send)} caratteri")
                    if attempt < max_attempts - 1:
                        continue
                else:
                    log(f"✅ Testo inserito correttamente: {len(inserted_text)} caratteri")
                    print(f"DEBUG: Testo inserito correttamente: {len(inserted_text)} caratteri")

                # 3. INVIO: Click sul pulsante con metodi multipli
                log("🔘 Click sul pulsante di invio...")
                print("DEBUG: Tentativo click pulsante invio...")

                # Attesa più lunga per il pulsante di invio
                send_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon"))
                )

                # Prova entrambi i metodi per maggiore affidabilità
                try:
                    # Metodo 1: Click standard
                    send_button.click()
                    log("✅ Click standard eseguito")
                    print("DEBUG: Click standard eseguito")
                except Exception as click_error:
                    log(f"⚠️ Errore click standard: {str(click_error)}")
                    print(f"DEBUG: Errore click standard: {str(click_error)}")
    
                    # Metodo 2: Click JavaScript
                    try:
                        driver.execute_script("arguments[0].click();", send_button)
                        log("✅ Click JavaScript eseguito")
                        print("DEBUG: Click JavaScript eseguito")
                    except Exception as js_error:
                        log(f"❌ Anche click JavaScript fallito: {str(js_error)}")
                        print(f"DEBUG: Anche click JavaScript fallito: {str(js_error)}")
        
                        # Metodo 3: Invio tramite tasto Enter
                        try:
                            input_box.send_keys(Keys.RETURN)
                            log("✅ Invio tramite tasto Enter")
                            print("DEBUG: Invio tramite tasto Enter")
                        except Exception as enter_error:
                            log(f"❌ Tutti i metodi di invio falliti: {str(enter_error)}")
                            print(f"DEBUG: Tutti i metodi di invio falliti: {str(enter_error)}")
                            raise Exception("Impossibile inviare il messaggio con nessun metodo")

                # 4. ATTESA RISPOSTA: Sistema di monitoraggio progressivo
                log("⏳ Attesa iniziale per la risposta (10 secondi)")
                print("DEBUG: Attesa iniziale per la risposta (10 secondi)")
                time.sleep(10)  # Attesa iniziale più lunga

                # Verifica che la richiesta non sia stata annullata immediatamente
                try:
                    error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'abortita') or contains(text(), 'aborted')]")
                    if error_elements:
                        log(f"❌ Richiesta abortita rilevata immediatamente per domanda #{question_number}")
                        print(f"DEBUG: Richiesta abortita rilevata immediatamente per domanda #{question_number}")

                        # INSERISCI QUESTO BLOCCO: pausa significativa prima di qualsiasi azione
                        log(f"⏳ Attesa prolungata (45 secondi) per stabilizzare l'interfaccia...")
                        time.sleep(45)  # Attesa molto più lunga prima di tentare la pulizia
    
                        log("🧹 Pulisco chat e riprovo lo stesso prompt")
    
                        # Pulisci la conversazione
                        if clear_chat(driver):
                            log("✅ Chat pulita con successo")
                            time.sleep(30)  # Attesa più lunga (30 secondi)
                        
                            if attempt < max_attempts - 1:
                                log(f"🔄 Riprovo domanda #{question_number}, tentativo {attempt+2}/{max_attempts}")
                                continue  # Riprova nello stesso ciclo di tentativi
                            else:
                                # Se tutti i tentativi sono falliti, prova un'ultima volta con una pagina pulita
                                log(f"⚠️ Ultimo tentativo dopo pulizia chat per domanda #{question_number}")
                                driver.get("https://genspark.ai")
                                time.sleep(15)
                                result = send_to_genspark(driver, text, log_callback, prompt_id, section_number, cooldown_manager, chat_manager, results_display)  # Chiamata ricorsiva
                                return result if result else update_ui_and_return(f"ERRORE: Richiesta abortita ripetutamente per domanda #{question_number}", success=False, message=f"Richiesta abortita ripetutamente per domanda #{question_number}")
                        else:
                            log("⚠️ Impossibile pulire la chat")
                            time.sleep(30)  # Attesa più lunga (30 secondi)
                        
                            if attempt < max_attempts - 1:
                                log(f"🔄 Nuovo tentativo per domanda #{question_number}")
                                continue
                            else:
                                return update_ui_and_return(f"ERRORE: Richiesta abortita ripetutamente per domanda #{question_number}", success=False, message=f"Richiesta abortita ripetutamente per domanda #{question_number}")
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
                                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                                if messages and len(messages) > 0:
                                    # Controlla se c'è un nuovo messaggio o un cambio nel conteggio
                                    if len(messages) > message_count:
                                        message_count = len(messages)
                                        log(f"📩 Nuovo messaggio rilevato: totale {message_count}")
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
                        log(f"⚠️ Errore nel recupero risposta: {str(e)}")
                        print(f"DEBUG: Errore nel recupero risposta: {str(e)}")
    
                    # 2. Metodo alternativo: JavaScript diretto
                    if not response:
                        try:
                            js_response = driver.execute_script("""
                                var messages = document.querySelectorAll('.message-content, .chat-message-item, .chat-wrapper .desc');
                                if (messages && messages.length > 0) {
                                    return messages[messages.length - 1].textContent;
                                }
                                return null;
                            """)
                        
                            if js_response:
                                response = js_response.strip()
                                log(f"📩 Risposta recuperata via JavaScript: {len(response)} caratteri")
                                print(f"DEBUG: Risposta recuperata via JavaScript: {len(response)} caratteri")
                        except Exception:
                            pass
    
                    # Se abbiamo ottenuto una risposta, analizzala
                    if response:
                        current_length = len(response)
                    
                        # Debug periodico della risposta in crescita
                        if cycle % 5 == 0:  # Ogni 5 cicli
                            preview = response[:150].replace('\n', ' ')
                            print(f"DEBUG: Risposta in corso - {current_length} caratteri - Preview: {preview}...")
                    
                        # Controlla gli errori tipici nella risposta
                        error_indicators = ["richiesta abortita", "request aborted", "troppo lungo", "too long", 
                                          "errore durante", "error during", "riprova più tardi", "try again later"]
                    
                        if any(indicator in response.lower() for indicator in error_indicators):
                            log(f"❌ Errore rilevato nella risposta: {response[:100]}...")
                            print(f"DEBUG: Errore rilevato nella risposta: {response[:100]}...")
                            if attempt < max_attempts - 1:
                                time.sleep(10)
                                break  # Esci dal ciclo e riprova l'invio
                            else:
                                error_msg = f"ERRORE: {response[:200]}"
                                return update_ui_and_return(error_msg, success=False, message="Errore rilevato nella risposta")
                    
                        # Controlla i terminatori espliciti
                        if "FINE_RISPOSTA" in response or "FINE" in response:
                            # Aggiungi debug dettagliato per il terminatore
                            terminator = "FINE_RISPOSTA" if "FINE_RISPOSTA" in response else "FINE"
                            terminator_pos = response.find(terminator)
                            context_before = response[max(0, terminator_pos-30):terminator_pos]
                            context_after = response[terminator_pos+len(terminator):min(len(response), terminator_pos+len(terminator)+30)]

                            log(f"🔍 TERMINATORE: '{terminator}' trovato alla posizione {terminator_pos} per domanda #{question_number}")
                            log(f"🔍 Contesto: ...{context_before}[{terminator}]{context_after}...")
                            print(f"DEBUG TERMINATORE: '{terminator}' trovato alla posizione {terminator_pos}")
                            print(f"DEBUG TERMINATORE: Contesto: ...{context_before}[{terminator}]{context_after}...")

                            # Continua con la logica esistente
                            log(f"✅ Terminatore esplicito trovato dopo {cycle+1} cicli per domanda #{question_number}")

                            # Pulisci la risposta rimuovendo il terminatore
                            if "FINE_RISPOSTA" in response:
                                response = response.split("FINE_RISPOSTA")[0].strip()
                            elif "FINE" in response:
                                response = response.split("FINE")[0].strip()

                            # Aggiungi una pausa di 30 secondi dopo ogni risposta completa
                            log("⏱️ Pausa di 30 secondi dopo risposta completa")
                            time.sleep(30)

                            return update_ui_and_return(response, success=True)
                        else:
                            # Se non viene trovato un terminatore ma la risposta è stabile
                            if stable_count >= 10:
                                log(f"⚠️ Risposta stabilizzata ma SENZA TERMINATORE per domanda #{question_number}")
    
                                # Verifica se abbiamo ancora tentativi disponibili per questa domanda
                                if attempt < max_attempts - 1:
                                    log(f"🔄 Risposta senza terminatore, riprovo domanda #{question_number}")
                        
                                    # Pulisci la chat prima di riprovare
                                    try:
                                        clear_chat(driver)
                                        log(f"🧹 Chat pulita prima di riprovare la domanda #{question_number}")
                                        time.sleep(5)  # Breve pausa dopo pulizia
                                    except Exception as clear_error:
                                        log(f"⚠️ Errore nella pulizia della chat: {str(clear_error)}")
                        
                                    # Attesa prima del nuovo tentativo
                                    wait_time = 15 * (attempt + 1)  # Aumenta il tempo di attesa ad ogni tentativo
                                    log(f"⏳ Attesa di {wait_time} secondi prima del nuovo tentativo...")
                                    time.sleep(wait_time)
                        
                                    break  # Esci dal ciclo di attesa e riprova la domanda
                                else:
                                    # Se abbiamo esaurito i tentativi, registra l'errore
                                    log(f"❌ Tutti i tentativi falliti per domanda #{question_number}: nessun terminatore trovato")
                                    return update_ui_and_return(response, success=False, 
                                                             message=f"Risposta senza terminatore per domanda #{question_number} dopo {max_attempts} tentativi")
                        
                        # Verifica stabilità della lunghezza
                        if current_length == last_length:
                            stable_count += 1
                            log(f"⏳ Risposta stabile: {stable_count}/5 cicli ({current_length} caratteri)")
                            print(f"DEBUG: Risposta stabile: {stable_count}/5 cicli ({current_length} caratteri)")
                        
                            if stable_count >= 10:  # 5 cicli di stabilità = risposta completa
                                log(f"✅ Risposta stabilizzata dopo {cycle+1} cicli")
                                print(f"DEBUG: Risposta stabilizzata dopo {cycle+1} cicli")
                                return update_ui_and_return(response)
                        else:
                            stable_count = 0
                            log(f"📝 Risposta in evoluzione: {current_length} caratteri (ciclo {cycle+1})")
                            print(f"DEBUG: Risposta in evoluzione: {current_length} caratteri (ciclo {cycle+1})")
                            last_length = current_length
                    else:
                        log(f"⚠️ Nessuna risposta rilevabile al ciclo {cycle+1}")
                        print(f"DEBUG: Nessuna risposta rilevabile al ciclo {cycle+1}")
    
                    # Controlla se abbiamo raggiunto un limite di contesto
                    
                    if cycle % 3 == 0:  # Ogni 3 cicli
                        if handle_context_limit(driver, log_callback):
                            log("♻️ Limite di contesto rilevato, nuovo tentativo...")
                            print("DEBUG: Limite di contesto rilevato, nuovo tentativo...")
                            return send_to_genspark(driver, section_to_send, log_callback, prompt_id, section_number, cooldown_manager, chat_manager, results_display)
    
                    # Attendi prima del prossimo ciclo
                    time.sleep(20)  # 20 secondi tra i cicli

                # Se siamo qui, il timeout è scaduto
                if response:
                    log(f"⚠️ Timeout ma risposta parziale disponibile: {len(response)} caratteri")
                    print(f"DEBUG: Timeout ma risposta parziale disponibile: {len(response)} caratteri")
                    print(f"DEBUG: Salvataggio risposta parziale - Lunghezza: {len(response)}")
                    print(f"DEBUG: Preview risposta parziale: {response[:200].replace(chr(10), ' ')}...")
                    return update_ui_and_return(response, message="Timeout, risposta parziale")
                else:
                    log("❌ Timeout senza risposta")
                    print("DEBUG: Timeout senza risposta")
                        
                    if attempt < max_attempts - 1:
                        retry_delay = 15 * (attempt + 1)  # Aumenta il ritardo ad ogni tentativo
                        log(f"🔄 Tentativo {attempt+2} dopo timeout - attesa {retry_delay} secondi")
                        print(f"DEBUG: Tentativo {attempt+2} dopo timeout - attesa {retry_delay} secondi")
                        time.sleep(retry_delay)
                    else:
                        error_msg = "TIMEOUT: Nessuna risposta ricevuta dopo ripetuti tentativi"
                        return update_ui_and_return(error_msg, success=False, message="Timeout senza risposta")

            except Exception as e:
                # Gestione errori specifici per sezione
                log(f"⚠️ Errore sezione, tentativo {attempt+1}: {str(e)}")
                print(f"DEBUG: Errore sezione, tentativo {attempt+1}: {str(e)}")
            
                # Cattura screenshot per debug
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot_path = f"error_section_try_{attempt+1}_{timestamp}.png"
                    driver.save_screenshot(screenshot_path)
                    log(f"📸 Screenshot: {screenshot_path}")
                    print(f"DEBUG: Screenshot errore: {screenshot_path}")
                except Exception:
                    pass
            
                if attempt < max_attempts - 1:
                    attempt_delay = 15 * (attempt + 1)
                    print(f"DEBUG: Attesa {attempt_delay}s prima del prossimo tentativo...")
                    time.sleep(attempt_delay)
                else:
                    log("❌ Tutti i tentativi falliti")
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
        log(f"❌ {error_message}")
        print(f"DEBUG: ERRORE CRITICO: {str(e)}")
    
        error_trace = traceback.format_exc()
        print(f"DEBUG: Traceback completo:\n{error_trace}")

        # Cattura screenshot finale
        try:
            screenshot_path = f"critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            driver.save_screenshot(screenshot_path)
            log(f"📸 Screenshot errore critico: {screenshot_path}")
            print(f"DEBUG: Screenshot errore critico: {screenshot_path}")
        except Exception:
            pass
    
        return update_ui_and_return(error_message, success=False, message=str(e))

def get_last_response(driver, log_callback=None):
    """
    Recupera l'ultima risposta dalla chat con controlli migliorati per terminazione.
    
    Args:
        driver: WebDriver di Selenium
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        str: Ultima risposta di Genspark o None se non trovata
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        # Prova diversi selettori per trovare i messaggi
        selectors = [
            "div.chat-wrapper div.desc > div > div > div",
            "div.chat-wrapper div.desc",
            "div.message-wrap div.message div.text-wrap",
            "div.message div.text-wrap",
            "div.desc",
            # Aggiungi selettori più specifici per Genspark
            ".message-content",
            ".message-bubble .content",
            ".chat-message-item .content"
        ]
    
        # Aggiungi un ritardo prima di cercare le risposte
        import time
        from selenium.webdriver.common.by import By
        
        time.sleep(2)
    
        for selector in selectors:
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                if messages:
                    # Prendi gli ultimi 2 messaggi (potrebbe esserci un messaggio di sistema)
                    for idx in range(min(2, len(messages))):
                        last_message = messages[-(idx+1)]
                        text = last_message.text.strip()
                    
                        # Verifica che non sia un messaggio di errore
                        if text and not ("errore" in text.lower() or 
                                         "abortita" in text.lower() or
                                         "rigenera" in text.lower()):
                            # Log di debug
                            print(f"DEBUG - Risposta trovata con selettore {selector}, lunghezza: {len(text)}")
                        
                            # NUOVO: Verifica terminatori espliciti
                            terminators = ["FINE", "FINE_RISPOSTA", "COMPLETATO", "ANALISI COMPLETATA"]
                            for terminator in terminators:
                                if terminator in text:
                                    # Tronca il testo al terminatore
                                    text = text[:text.find(terminator)].strip()
                                    # Log per indicare che è stata trovata una terminazione esplicita
                                    print(f"DEBUG - Terminatore '{terminator}' trovato nella risposta")
                                    return text
                        
                            return text
            except Exception as e:
                print(f"DEBUG - Errore con selettore {selector}: {str(e)}")
                continue
    
        # Se arriviamo qui, proviamo un approccio JavaScript diretto
        try:
            js_result = driver.execute_script("""
                // Recupera tutte le risposte visibili
                var messages = document.querySelectorAll('.message-content, .chat-message-item, .chat-wrapper .desc');
                if (messages && messages.length > 0) {
                    return messages[messages.length - 1].textContent;
                }
                return null;
            """)
        
            if js_result:
                print(f"DEBUG - Risposta trovata tramite JavaScript: {len(js_result)} caratteri")
                return js_result
        except Exception as e:
            print(f"DEBUG - Errore nel recupero JavaScript: {str(e)}")
    
        print("DEBUG - Nessuna risposta trovata con alcun metodo")
        return None

    except Exception as e:
        if log_callback:
            log_callback(f"Errore nel recupero della risposta: {str(e)}")
        print(f"ERROR - Eccezione globale in get_last_response: {str(e)}")
        return None

def check_for_generation_error(response):
    """
    Controlla se la risposta contiene errori di generazione.

    Args:
        response: Risposta da controllare
    
    Returns:
        bool: True se c'è un errore, False altrimenti
        str: Messaggio di errore o None
    """
    error_patterns = [
        "richiesta abortita", 
        "request aborted", 
        "troppo lungo", 
        "too long", 
        "I'm sorry, but I'm unable to generate",
        "I apologize, but I cannot",
        "As an AI assistant, I cannot",
        "I cannot comply with this request",
        "I'm unable to provide",
        "I cannot fulfill this request"
    ]

    if not response:
        return True, "Risposta vuota"

    for pattern in error_patterns:
        if pattern.lower() in response.lower():
            return True, f"Errore di generazione: {pattern}"

    return False, None

def handle_consecutive_errors(driver, prompt_text, max_retries=3, log_callback=None):
    """
    Gestisce errori consecutivi tentando approcci alternativi
    
    Args:
        driver: WebDriver di Selenium
        prompt_text: Testo del prompt
        max_retries: Numero massimo di tentativi
        log_callback: Funzione di callback per il logging
        
    Returns:
        str: Risposta recuperata o messaggio di errore
    """
    # Importazioni necessarie
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from ai_interfaces.browser_manager import handle_context_limit
    from ai_interfaces.genspark_driver import get_last_response
    
    # Funzione di logging
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    log(f"🔄 Tentativo di ripristino dopo errori consecutivi ({max_retries} tentativi)")
    
    for retry in range(max_retries):
        log(f"Tentativo di recupero {retry+1}/{max_retries}")
    
        # Prova reset del contesto
        if handle_context_limit(driver, log_callback):
            log("✅ Contesto resettato con successo")
        
            # Riprova con lo stesso prompt
            input_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper textarea"))
            )
            input_box.clear()
            time.sleep(1)
        
            # Inserisci il prompt originale (possibilmente modificato)
            modified_prompt = f"{prompt_text}\n\n(Tentativo di recupero {retry+1})"
            log(f"🔄 Reinvio prompt modificato: {modified_prompt[:50]}...")
        
            # Invia e attendi
            input_box.send_keys(modified_prompt)
            time.sleep(1)
        
            # Trova e clicca il pulsante di invio
            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon"))
            )
            send_button.click()
        
            # Attendi
            time.sleep(20)
        
            # Verifica la risposta
            response = get_last_response(driver, log_callback)
            if response and len(response) > 100 and "errore" not in response.lower():
                log("✅ Recupero riuscito!")
                return response
    
        # Aumenta il tempo di attesa tra i tentativi
        wait_time = 10 + (retry * 5)
        log(f"⏱️ Attesa {wait_time} secondi prima del prossimo tentativo...")
        time.sleep(wait_time)

    log("❌ Tutti i tentativi di recupero falliti")
    return "[ERRORE: Impossibile ottenere una risposta valida dopo multipli tentativi]"

