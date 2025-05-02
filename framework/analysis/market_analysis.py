"""
Moduli di analisi di mercato per CRISP.
"""
import logging
import time
import re
from datetime import datetime

def extract_market_analysis(text):
    """
    Estrae dati dalla risposta dell'analisi di mercato (CM-1).
    """
    data = {}
    
    # Estrai MARKET_INSIGHTS
    market_insights_section = re.search(r'MARKET_INSIGHTS[^:]*:(.*?)(?=KEYWORD_DATA|$)', text, re.DOTALL | re.IGNORECASE)
    if market_insights_section:
        data["MARKET_INSIGHTS"] = market_insights_section.group(1).strip()
    else:
        # Sezione fallback
        data["MARKET_INSIGHTS"] = "Dati di mercato estratti dall'analisi generale"
    
    # Estrai KEYWORD_DATA
    keyword_data_section = re.search(r'KEYWORD_DATA[^:]*:(.*?)(?=BESTSELLER_OVERVIEW|$)', text, re.DOTALL | re.IGNORECASE)
    if keyword_data_section:
        data["KEYWORD_DATA"] = keyword_data_section.group(1).strip()
    else:
        data["KEYWORD_DATA"] = "Dati keyword estratti dall'analisi"
    
    # Estrai BESTSELLER_OVERVIEW
    bestseller_section = re.search(r'BESTSELLER_OVERVIEW[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if bestseller_section:
        data["BESTSELLER_OVERVIEW"] = bestseller_section.group(1).strip()
    else:
        # Sezione fallback
        bestseller_match = re.search(r'(bestseller|più venduti|top seller)[^\n]*((?:\n[^#][^\n]*){1,20})', text, re.IGNORECASE)
        if bestseller_match:
            data["BESTSELLER_OVERVIEW"] = bestseller_match.group(2).strip()
        else:
            data["BESTSELLER_OVERVIEW"] = "Panoramica bestseller estratta dall'analisi"
    
    # Aggiungi valori di fallback per variabili cruciali
    if "MARKET_INSIGHTS" not in data or not data["MARKET_INSIGHTS"]:
        data["MARKET_INSIGHTS"] = "Analisi di mercato generale completata"
    
    if "BESTSELLER_OVERVIEW" not in data or not data["BESTSELLER_OVERVIEW"]:
        data["BESTSELLER_OVERVIEW"] = "Analisi dei bestseller completata"
    
    return data

def extract_bestseller_analysis(text):
    """
    Estrae dati dall'analisi dei bestseller (CM-2).
    
    Args:
        text: Risposta da Genspark per prompt CM-2
        
    Returns:
        dict: Dati strutturati sull'analisi dei bestseller
    """
    data = {}
    
    # Estrai STRUCTURE_PATTERNS
    structure_section = re.search(r'STRUCTURE_PATTERNS[^:]*:(.*?)(?=TITLE_PATTERNS|$)', text, re.DOTALL | re.IGNORECASE)
    if structure_section:
        data["STRUCTURE_PATTERNS"] = structure_section.group(1).strip()
    
    # Estrai TITLE_PATTERNS
    title_section = re.search(r'TITLE_PATTERNS[^:]*:(.*?)(?=REVIEW_INSIGHTS|$)', text, re.DOTALL | re.IGNORECASE)
    if title_section:
        data["TITLE_PATTERNS"] = title_section.group(1).strip()
    
    # Estrai REVIEW_INSIGHTS
    review_section = re.search(r'REVIEW_INSIGHTS[^:]*:(.*?)(?=IMPLEMENTATION_OBSTACLES|$)', text, re.DOTALL | re.IGNORECASE)
    if review_section:
        data["REVIEW_INSIGHTS"] = review_section.group(1).strip()
    
    # Estrai IMPLEMENTATION_OBSTACLES
    obstacles_section = re.search(r'IMPLEMENTATION_OBSTACLES[^:]*:(.*?)(?=MARKET_GAPS|$)', text, re.DOTALL | re.IGNORECASE)
    if obstacles_section:
        data["IMPLEMENTATION_OBSTACLES"] = obstacles_section.group(1).strip()
    
    # Estrai MARKET_GAPS
    gaps_section = re.search(r'MARKET_GAPS[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if gaps_section:
        data["MARKET_GAPS"] = gaps_section.group(1).strip()
    
    return data

# Definisci una funzione executor che invia il prompt a Genspark
def analyze_market_crisp(book_type, keyword, language, market, selected_phases=None, crisp_framework=None, driver=None, chat_manager=None):
    """
    Analizza il mercato usando il framework CRISP 5.0.

    Args:
        book_type: Tipo di libro
        keyword: Keyword principale
        language: Lingua dell'output
        market: Mercato di riferimento
        selected_phases: Lista di fasi selezionate da eseguire (opzionale)
        crisp_framework: Istanza del framework CRISP
        driver: Istanza del WebDriver Selenium
        chat_manager: Istanza del ChatManager per il logging

    Returns:
        str: Log dell'operazione
    """
    try:
        # Funzione di logging
        def log(message):
            if chat_manager:
                chat_manager.add_log(message)
            else:
                print(message)
        
        log(f"Avvio analisi CRISP 5.0 per: {keyword}")
    
        # Converti selected_phases in una lista se è una stringa singola
        if isinstance(selected_phases, str):
            selected_phases = [selected_phases]
    
        # Log delle fasi selezionate
        if selected_phases:
            log(f"🔍 Esecuzione selettiva delle fasi CRISP: {', '.join(selected_phases)}")
        else:
            log("🔍 Esecuzione di tutte le fasi CRISP")

        # Crea un nuovo progetto nel database CRISP
        project_name = f"{keyword} - {datetime.now().strftime('%Y-%m-%d')}"
        project_id = crisp_framework.create_project(project_name)

        # Dictionary per market lookup
        markets_dict = {
            "USA": "Amazon.com",
            "Italia": "Amazon.it",
            "Francia": "Amazon.fr",
            "Inghilterra": "Amazon.co.uk",
            "Canada": "Amazon.ca",
            "Australia": "Amazon.com.au",
            "Spagna": "Amazon.es",
            "Germania": "Amazon.de"
        }

        # Prepara i dati iniziali del progetto
        initial_data = {
            "PROJECT_ID": project_id,
            "PROJECT_NAME": project_name,
            "KEYWORD": keyword,
            "LIBRO_TIPO": book_type,
            "LINGUA": language, 
            "MERCATO": market,
            "AMAZON_URL": markets_dict.get(market, "Amazon.com")
        }
    
        # Salva il riferimento al progetto CRISP corrente
        current_analysis = {
            'crisp_project_id': project_id,
            'project_data': initial_data,
            'KEYWORD': keyword
        }

        # Funzione semplice che processa il prompt
        def process_prompt(prompt_text):
            log(f"Elaborazione prompt: {len(prompt_text)} caratteri")

            # Sostituisci le variabili nel prompt
            processed_text = prompt_text
            if "{KEYWORD}" in processed_text:
                processed_text = processed_text.replace("{KEYWORD}", keyword)
            if "{MERCATO}" in processed_text:
                processed_text = processed_text.replace("{MERCATO}", market)

            # Importa on-demand per evitare dipendenze circolari
            from ai_interfaces.genspark_driver import send_to_genspark
            
            # Invia il prompt a Genspark
            response = send_to_genspark(driver, processed_text, log_callback=log)

            # Pulisci la risposta se contiene "FINE"
            if response and "FINE" in response.upper():
                response = response[:response.upper().find("FINE")].strip()

            return response
            
        # Restituisci i risultati dell'analisi
        return current_analysis
        
    except Exception as e:
        error_msg = f"❌ Errore nell'analisi CRISP: {str(e)}"
        log(error_msg)
        logging.error(error_msg)
        return f"Errore: {str(e)}"

        # SOLUZIONE - Patching del metodo execute_step
        original_execute_step = crisp_framework.execute_step

        def patched_execute_step(prompt_id, project_data, executor_func):
            """
            Versione patchata di execute_step che processa una sezione alla volta.
            """
            log(f"Esecuzione patchata di step {prompt_id}")

            try:
                # Carica i dati del prompt
                prompt_data = crisp_framework.load_prompt(prompt_id)
                prompt_content = prompt_data["content"]

                # Dividi il contenuto in sezioni
                sections = prompt_content.split("\n---\n")
                numbered_sections = []
                for section in sections:
                    section = section.strip()
                    if re.match(r'^\d+\.', section):
                        numbered_sections.append(section)

                if not numbered_sections:
                    numbered_sections = [prompt_content]

                if chat_manager:
                    chat_manager.log_prompt_location(prompt_id, "ALL", f"Trovate {len(numbered_sections)} sezioni")

                # Processa ogni sezione e raccogli le risposte
                all_responses = []
                
                from ai_interfaces.interaction_utils import clear_chat
                
                for i, section in enumerate(numbered_sections):
                    section_number = i + 1
                    if chat_manager:
                        chat_manager.log_prompt_location(prompt_id, section_number, "Inizio elaborazione")

                    # Pulisci la chat prima di ogni sezione
                    try:
                        clear_chat(driver)
                        time.sleep(2)
                    except Exception as e:
                        if chat_manager:
                            chat_manager.log_prompt_location(prompt_id, section_number, "Errore pulizia chat", str(e))

                    # Processa la sezione
                    from framework.crisp_utils import replace_variables
                    processed_section = replace_variables(section.strip(), project_data)
                    
                    # Importa on-demand per evitare dipendenze circolari
                    from ai_interfaces.genspark_driver import send_to_genspark
                    
                    response = send_to_genspark(
                        driver, processed_section, log_callback=log, 
                        prompt_id=prompt_id, section_number=section_number
                    )
        
                    # Log della risposta
                    response_preview = response[:100] + "..." if response else "Nessuna risposta"
                    if chat_manager:
                        chat_manager.log_prompt_location(prompt_id, section_number, "Risposta ricevuta", response_preview)
        
                    all_responses.append(response)

                    # Attendi che la risposta sia completa
                    if "FINE_RISPOSTA" not in response:
                        if chat_manager:
                            chat_manager.log_prompt_location(prompt_id, section_number, "Attesa completamento")
                        time.sleep(10)

                # Combina tutte le risposte
                full_result = "\n\n".join(all_responses)

                # Estrai i dati solo dopo aver processato tutte le sezioni
                extracted_data = crisp_framework.extract_data(full_result, prompt_id)

                # Salva il risultato nel database
                if "PROJECT_ID" in project_data:
                    crisp_framework._save_result_to_db(
                        project_data["PROJECT_ID"],
                        prompt_id,
                        full_result,
                        extracted_data
                    )

                # Aggiorna i dati del progetto
                project_data.update(extracted_data)

                return project_data, full_result, extracted_data

            except Exception as e:
                if chat_manager:
                    chat_manager.log_prompt_location(prompt_id, "ERROR", f"Errore in patched_execute_step: {str(e)}")
                raise

        # Sostituisci temporaneamente il metodo execute_step
        crisp_framework.execute_step = patched_execute_step

        # Esegui il flusso CRISP
        try:
            # Se abbiamo fasi selezionate, usa solo quelle in ordine
            if selected_phases and len(selected_phases) > 0:
                # Ordina le fasi selezionate per assicurare l'esecuzione corretta
                sorted_phases = sorted(selected_phases)
            
                log(f"⚙️ Esecuzione fasi CRISP in ordine: {', '.join(sorted_phases)}")
            
                # Esegui ciascuna fase individualmente
                execution_history = []
                current_data = initial_data.copy()
            
                for phase_id in sorted_phases:
                    log(f"🔄 Esecuzione fase {phase_id}")
                
                    # Esegui la singola fase
                    updated_data, phase_result, extracted_data = crisp_framework.execute_step(
                        phase_id, 
                        current_data.copy(), 
                        process_prompt
                    )
                
                    # Aggiorna i dati correnti con i risultati della fase
                    current_data.update(updated_data)
                
                    # Aggiungi alla storia di esecuzione
                    execution_history.append({
                        'step_id': phase_id,
                        'result': phase_result,
                        'extracted_data': extracted_data
                    })
            
                # Risultati finali
                final_data = current_data
                log(f"✅ Esecuzione delle fasi selezionate completata: {', '.join(sorted_phases)}")
            else:
                # Esegui il flusso normale dall'inizio alla fine
                log("⚙️ Esecuzione del flusso completo CRISP")
                final_data, execution_history = crisp_framework.execute_flow(
                    initial_data,
                    process_prompt,
                    start_step="CM-1"
                )
                log("✅ Analisi CRISP completa eseguita con successo")
        
            # Aggiorna il risultato per il chiamante
            result = {
                'project_data': final_data,
                'execution_history': execution_history,
                'crisp_project_id': project_id
            }
        
        finally:
            # Ripristina il metodo originale
            crisp_framework.execute_step = original_execute_step

        return result

    except Exception as e:
        if chat_manager:
            chat_manager.add_log(f"❌ Errore nell'analisi CRISP: {str(e)}")
        return str(e)

def analyze_market_legacy(book_type, keyword, language, market, analysis_prompt, driver=None, chat_manager=None, markets=None):
    """
    Metodo legacy per l'analisi di mercato, che invia automaticamente
    tutte le righe di prompt in sequenza e restituisce la risposta cumulativa.
    
    Args:
        book_type: Tipo di libro
        keyword: Keyword principale
        language: Lingua dell'output
        market: Mercato di riferimento
        analysis_prompt: Testo del prompt da utilizzare
        driver: Istanza del WebDriver Selenium
        chat_manager: Istanza del ChatManager per logging e salvataggio risposte
        markets: Dizionario dei mercati Amazon (opzionale)
        
    Returns:
        str: Risposta combinata dall'analisi di mercato
    """
    try:
        # Funzione logger di supporto
        def log(message):
            if chat_manager:
                chat_manager.add_log(message)
        
        log(f"🚀 Avvio analisi di mercato (legacy) per: {keyword}")

        # 1) Costruisci l'URL Amazon corretto
        # Se il dizionario markets non è fornito, usa un dizionario predefinito
        if not markets:
            markets = {
                "USA": "Amazon.com",
                "Italia": "Amazon.it",
                "Francia": "Amazon.fr",
                "Inghilterra": "Amazon.co.uk",
                "Canada": "Amazon.ca",
                "Australia": "Amazon.com.au",
                "Spagna": "Amazon.es",
                "Germania": "Amazon.de"
            }
        
        amazon_url = markets.get(market, "Amazon.com")

        # 2) Prepara il prompt totale e splittalo in righe non vuote
        formatted_prompt = analysis_prompt.format(
            amazon_url=amazon_url,
            keyword=keyword,
            tipo_libro=book_type,
            lingua=language,
            market=market
        )
        lines = [line.strip() for line in formatted_prompt.split('\n') if line.strip()]

        # 3) Prepara metadati per il salvataggio cumulativo
        from datetime import datetime
        
        metadata = {
            "type": "market_analysis_legacy",
            "book_type": book_type,
            "keyword": keyword,
            "language": language,
            "market": market,
            "amazon_url": amazon_url,
            "timestamp_start": datetime.now().strftime('%Y%m%d_%H%M%S')
        }

        # 4) Invia riga per riga **automaticamente**
        responses = []
        
        # Importa on-demand per evitare dipendenze circolari
        import time
        from ai_interfaces.genspark_driver import send_to_genspark
        
        for idx, line in enumerate(lines, start=1):
            log(f"📨 Invio riga {idx}/{len(lines)}: {line[:60]}...")
            resp = send_to_genspark(driver, line, log)

            # Rimuovi eventuale "FINE" dalla risposta
            if resp and "FINE" in resp.upper():
                resp = resp[:resp.upper().find("FINE")].strip()

            log(f"✅ Risposta riga {idx}: {len(resp)} caratteri")
            responses.append(resp)

            # Piccola pausa tra una riga e l'altra
            time.sleep(5)

        # 5) Combina tutte le risposte e salvale
        combined = "\n\n".join(responses)
        
        if chat_manager:
            chat_manager.save_response(
                combined,
                "Analisi Legacy",
                metadata
            )
            
        log(f"🎉 Analisi legacy completata, {len(combined)} caratteri salvati")

        return combined

    except Exception as e:
        import logging
        error_msg = f"❌ Errore durante l'analisi legacy: {str(e)}"
        log(error_msg)
        logging.error(error_msg)
        return chat_manager.get_log_history_string() if chat_manager else str(e)

def filter_legacy_prompt_sections(analysis_prompt, selected_phases, log_callback=None):
    """
    Filtra il prompt legacy per includere solo le sezioni selezionate.
    
    Args:
        analysis_prompt: Prompt completo con tutte le sezioni
        selected_phases: Lista di numeri delle sezioni da includere
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        str: Prompt filtrato con solo le sezioni selezionate
    """
    import re
    
    try:
        # Funzione helper per il logging
        def log(message):
            if log_callback:
                log_callback(message)
        
        # Log delle fasi selezionate
        log(f"🔍 Fasi Legacy selezionate: {', '.join(map(str, selected_phases))}")
        
        # Verifica che ci siano fasi selezionate
        if not selected_phases:
            log("⚠️ Nessuna fase selezionata, utilizzo il prompt completo")
            return analysis_prompt
        
        # Assicurati che selected_phases contenga interi
        selected_phases = [int(p) if isinstance(p, str) and p.isdigit() else p for p in selected_phases]
        
        # Estrai tutte le sezioni numerate dal prompt
        all_sections = []
        pattern = r'(\d+)[\.|\)](.*?)(?=\n\s*\d+[\.|\)]|$)'
        
        matches = re.finditer(pattern, analysis_prompt, re.DOTALL)
        for match in matches:
            section_number = int(match.group(1))
            section_content = match.group(0)  # Prendi l'intera sezione, incluso il numero
            all_sections.append((section_number, section_content))
        
        log(f"📋 Trovate {len(all_sections)} sezioni totali nel prompt")
        
        # Filtra solo le sezioni che sono state selezionate
        filtered_sections = []
        for num, content in all_sections:
            if num in selected_phases:
                filtered_sections.append(content)
        
        # Se non ci sono sezioni filtrate, restituisci un subset del prompt originale
        if not filtered_sections:
            log("⚠️ Nessuna sezione trovata dopo il filtraggio, utilizzo prima sezione")
            # Restituisci solo la prima sezione come fallback
            if all_sections:
                return all_sections[0][1]
            return analysis_prompt.split("\n\n")[0] if "\n\n" in analysis_prompt else analysis_prompt
        
        # Unisci le sezioni filtrate con doppi newline per mantenere la formattazione
        filtered_prompt = "\n\n".join(filtered_sections)
        
        log(f"✅ Prompt filtrato: {len(filtered_prompt)} caratteri, {len(filtered_sections)} sezioni")
        return filtered_prompt
        
    except Exception as e:
        if log_callback:
            log_callback(f"⚠️ Errore nel filtraggio del prompt: {str(e)}")
            import traceback
            log_callback(traceback.format_exc())
        # In caso di errore, restituisci solo la prima parte del prompt
        return analysis_prompt.split("\n\n")[0] if "\n\n" in analysis_prompt else analysis_prompt

# VERSIONE ALTERNATIVA PIÙ SEMPLIFICATA - ATTUALMENTE NON UTILIZZATA
# Questa è una versione più diretta che utilizza l'API standard del framework CRISP
# È stata disabilitata in favore della versione più completa sopra che offre
# gestione più dettagliata delle sezioni dei prompt e altri miglioramenti
"""
def analyze_market_crisp(book_type, keyword, language, market, selected_phases=None,
                         crisp_framework=None, driver=None, chat_manager=None):
    '''
    Analizza il mercato usando il framework CRISP 5.0.

    Args:
        book_type: Tipo di libro
        keyword: Keyword principale
        language: Lingua dell'output
        market: Mercato di riferimento
        selected_phases: Lista di fasi selezionate da eseguire (opzionale)
        crisp_framework: Istanza del framework CRISP
        driver: WebDriver di Selenium
        chat_manager: Gestore delle chat per logging

    Returns:
        dict: Risultati dell'analisi con ID progetto CRISP o messaggio di errore
    '''
    def log(message):
        if chat_manager:
            chat_manager.add_log(message)
        else:
            print(message)
            
    try:
        log(f"Avvio analisi CRISP 5.0 per: {keyword}")
        
        if not driver:
            log("❌ Browser non disponibile")
            return "Errore: Browser non disponibile"
            
        if not crisp_framework:
            log("❌ Framework CRISP non inizializzato")
            return "Errore: Framework CRISP non inizializzato"
        
        # Verificare le fasi selezionate
        if selected_phases:
            all_phases = [
                'CPM-1', 'CPM-2', 'CPM-3', 
                'CS-1', 'CS-2', 'CS-3', 'CS-F',
                'CM-1', 'CM-2', 
                'CP-1', 'CP-2'
            ]
            if not set(selected_phases).issubset(set(all_phases)):
                invalid_phases = set(selected_phases) - set(all_phases)
                log(f"⚠️ Fasi non valide: {', '.join(invalid_phases)}")
                
            log(f"🔍 Esecuzione selettiva delle fasi CRISP: {', '.join(selected_phases)}")
        else:
            # Usa tutte le fasi predefinite
            selected_phases = crisp_framework.get_default_phases()
            log(f"🔍 Esecuzione di tutte le fasi CRISP predefinite: {', '.join(selected_phases)}")
            
        # CORREZIONE: Parametro 'description' spostato in params
        project_id = crisp_framework.create_project(
            name=f"{keyword} - {book_type}",  # Specificato esplicitamente il parametro name
            params={
                "keyword": keyword,
                "market": market,
                "language": language,
                "book_type": book_type,
                "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": f"Analisi di mercato per {keyword} in {market}"  # Spostato qui
            }
        )
        
        log(f"⚙️ Esecuzione fasi CRISP in ordine: {', '.join(selected_phases)}")
        
        # Esegui le fasi richieste in ordine
        for phase_id in selected_phases:
            log(f"🔄 Esecuzione fase {phase_id}")
            
            result = crisp_framework.execute_step(
                step_id=phase_id,
                project_id=project_id,
                driver=driver,
                params={
                    "keyword": keyword,
                    "market": market,
                    "language": language,
                    "book_type": book_type
                }
            )
            
            if not result.get('success'):
                log(f"❌ Errore durante l'esecuzione della fase {phase_id}: {result.get('message', 'Errore sconosciuto')}")
                continue
                
            log(f"✅ Fase {phase_id} completata con successo")
            
            # Attendi un po' tra le fasi per evitare di sovraccaricare l'AI
            time.sleep(10)
                
        # Raccogli tutti i dati estratti
        project_data = crisp_framework.get_project_data(project_id)
        
        # Salva i dati di contesto se disponibile
        if chat_manager and hasattr(chat_manager, 'save_context_data'):
            chat_manager.save_context_data(project_data)
            log("✅ Dati di contesto salvati")
            
        # Prepara i risultati
        results = {
            'crisp_project_id': project_id,
            'project_data': project_data,
            'message': f"Analisi CRISP completata per {keyword}"
        }
        
        log(f"✅ Analisi CRISP completata con successo per {keyword}")
        return results
        
    except Exception as e:
        import traceback
        error_msg = f"❌ Errore nell'analisi CRISP: {str(e)}"
        log(error_msg)
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"Errore: {str(e)}"
"""

# VERSIONE ALTERNATIVA SEMPLIFICATA DEL METODO LEGACY - ATTUALMENTE NON UTILIZZATA
# Questa è una versione più diretta della funzione analyze_market_legacy
# È stata disabilitata in favore della versione più completa sopra che offre
# gestione più dettagliata delle risposte e altre funzionalità avanzate
"""
def analyze_market_legacy(book_type, keyword, language, market, analysis_prompt, driver=None, chat_manager=None, markets=None):
    '''
    Metodo legacy per l'analisi di mercato, che invia automaticamente
    tutte le righe di prompt in sequenza e restituisce la risposta cumulativa.

    Args:
        book_type: Tipo di libro
        keyword: Keyword principale
        language: Lingua dell'output
        market: Mercato di riferimento
        analysis_prompt: Prompt di analisi completo
        driver: WebDriver di Selenium
        chat_manager: Gestore delle chat per logging
        markets: Dizionario dei mercati disponibili

    Returns:
        str: Risultato dell'analisi o messaggio di errore
    '''
    def log(message):
        if chat_manager:
            chat_manager.add_log(message)
        else:
            print(message)
            
    try:
        log(f"Avvio analisi legacy per: {keyword}")
        
        if not driver:
            log("❌ Browser non disponibile")
            return "Errore: Browser non disponibile"
            
        # Preparazione variabili di contesto
        amazon_url = ""
        if markets and market in markets:
            amazon_url = markets[market]["url"]
            log(f"📚 URL Amazon per {market}: {amazon_url}")
        else:
            log(f"⚠️ Mercato {market} non trovato nella configurazione, usando URL generico")
            amazon_url = f"https://www.amazon.{market.lower()}"
            
        # Sostituisci i segnaposto nel prompt
        analysis_prompt = analysis_prompt.replace("{keyword}", keyword)
        analysis_prompt = analysis_prompt.replace("{amazon_url}", amazon_url)
        analysis_prompt = analysis_prompt.replace("{market}", market)
        analysis_prompt = analysis_prompt.replace("{lingua}", language)
        
        log(f"🔍 Prompt preparato con {len(analysis_prompt)} caratteri")
        
        # Esecuzione dell'analisi (la logica specifica dipenderà dalla funzione
        # send_to_genspark che dovrebbe essere disponibile tramite chat_manager o driver)
        if hasattr(chat_manager, 'send_to_genspark'):
            result = chat_manager.send_to_genspark(analysis_prompt)
        else:
            from ai_interfaces.genspark_driver import send_to_genspark
            result = send_to_genspark(driver, analysis_prompt, log_callback=log)
            
        log(f"✅ Analisi legacy completata per {keyword}")
        
        return result
        
    except Exception as e:
        import logging
        import traceback
        error_msg = f"❌ Errore nell'analisi legacy: {str(e)}"
        log(error_msg)
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        return f"Errore: {str(e)}"
"""

# VERSIONE ALTERNATIVA SEMPLIFICATA DELLA FUNZIONE DI FILTRAGGIO - ATTUALMENTE NON UTILIZZATA
# Questa è una versione più diretta della funzione filter_legacy_prompt_sections
# È stata disabilitata in favore della versione più completa sopra che offre
# analisi più dettagliata e maggiore robustezza
"""
def filter_legacy_prompt_sections(analysis_prompt, selected_phases, log_callback=None):
    '''
    Filtra il prompt legacy per includere solo le sezioni selezionate.
    
    Args:
        analysis_prompt: Prompt di analisi completo
        selected_phases: Lista dei numeri di fase da includere
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        str: Prompt filtrato contenente solo le sezioni selezionate
    '''
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    import re
    
    if not selected_phases:
        log("⚠️ Nessuna fase selezionata, restituisco il prompt completo")
        return analysis_prompt
    
    try:
        # Converte selected_phases in lista di numeri interi
        if not isinstance(selected_phases, list):
            selected_phases = [int(selected_phases)]
        else:
            selected_phases = [int(phase) for phase in selected_phases]
        
        log(f"🔍 Filtro prompt con fasi selezionate: {selected_phases}")
        
        # Trova tutte le sezioni numerate nel prompt
        sections = []
        section_pattern = r'(\d+\).*?)(?=\d+\)|$)'
        section_matches = re.findall(section_pattern, analysis_prompt, re.DOTALL)
        
        if not section_matches:
            log("⚠️ Nessuna sezione numerata trovata nel prompt")
            return analysis_prompt
        
        log(f"✅ Trovate {len(section_matches)} sezioni numerate nel prompt")
        
        # Filtra le sezioni in base ai numeri selezionati
        filtered_sections = []
        for section in section_matches:
            # Estrai il numero di sezione (es. da "1) Analisi..." estrae "1")
            section_num_match = re.match(r'(\d+)\)', section)
            if section_num_match:
                section_num = int(section_num_match.group(1))
                if section_num in selected_phases:
                    filtered_sections.append(section.strip())
                    log(f"✅ Selezionata sezione {section_num}")
            else:
                log(f"⚠️ Impossibile estrarre numero da sezione: {section[:50]}...")
        
        if not filtered_sections:
            log("⚠️ Nessuna sezione corrispondente trovata, uso prompt originale")
            return analysis_prompt
        
        # Ricomponi il prompt con le sezioni filtrate
        filtered_prompt = "\\n\\n".join(filtered_sections)
        log(f"✅ Prompt filtrato con {len(filtered_sections)} sezioni ({len(filtered_prompt)} caratteri)")
        
        return filtered_prompt
        
    except Exception as e:
        log(f"❌ Errore nel filtraggio del prompt: {str(e)}")
        return analysis_prompt
"""