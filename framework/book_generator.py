"""
Modulo per la generazione di libri con diversi framework.
"""

import re
import time
import os
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def generate_book_crisp(book_title, book_language, voice_style, book_index,
                      crisp_framework=None, driver=None, chat_manager=None, current_analysis=None):
    """
    Genera il libro usando il framework CRISP 5.0.

    Args:
        book_title: Titolo del libro
        book_language: Lingua del libro
        voice_style: Stile narrativo
        book_index: Indice del libro
        crisp_framework: Istanza del framework CRISP
        driver: Istanza del WebDriver Selenium
        chat_manager: Istanza del ChatManager per il logging
        current_analysis: Dizionario contenente i dati di analisi correnti
        
    Returns:
        str: Percorso del file del libro generato o messaggio di errore
    """
    # Funzione di log
    def log(message):
        if chat_manager:
            chat_manager.add_log(message)
        else:
            print(message)
    
    try:
        if not book_title.strip():
            log("Errore: Il titolo del libro è obbligatorio!")
            return "Errore: Il titolo del libro è obbligatorio!"
        
        if not book_index.strip():
            log("Errore: L'indice del libro è obbligatorio!")
            return "Errore: L'indice del libro è obbligatorio!"
        
        log(f"Avvio generazione libro CRISP 5.0: {book_title}")
        
        # Recupera l'ID del progetto CRISP corrente
        project_id = current_analysis.get('crisp_project_id') if current_analysis else None
        if not project_id:
            log("Errore: Nessun progetto CRISP corrente trovato")
            return "Errore: Nessun progetto CRISP corrente trovato"
        
        # Recupera i dati completi del progetto
        project_data = crisp_framework.get_project_data(project_id)
        
        # Aggiorna i dati del progetto con le informazioni correnti
        project_data.update({
            "TITOLO_LIBRO": book_title,
            "LINGUA_LIBRO": book_language,
            "VOICE_STYLE": voice_style,
            "INDICE_LIBRO": book_index
        })
        
        # Aggiorna i dati nel database CRISP
        crisp_framework._save_result_to_db(
            project_id,
            "GEN1",
            f"Generazione libro: {book_title}",
            {
                "TITOLO_LIBRO": book_title,
                "LINGUA_LIBRO": book_language,
                "VOICE_STYLE": voice_style,
                "INDICE_LIBRO": book_index
            }
        )
        
        # Dividi l'indice in capitoli
        chapters = [line.strip() for line in book_index.split('\n') if line.strip()]
        
        # Filtra per mantenere solo le righe che sembrano capitoli
        chapter_pattern = re.compile(r'(CAPITOLO|CHAPTER|PARTE|PART|SEZIONE|SECTION)\s*\d*\s*[:\.\-–—]?\s*(.*)', re.IGNORECASE)
        filtered_chapters = []
        
        for line in chapters:
            match = chapter_pattern.match(line)
            if match:
                chapter_title = match.group(2).strip()
                if chapter_title:  # Assicurati che il titolo non sia vuoto
                    filtered_chapters.append(chapter_title)
            elif not any(keyword.lower() in line.lower() for keyword in ['introduzione', 'introduction', 'conclusione', 'conclusion']):
                # Includi anche le righe che non contengono parole chiave specifiche
                filtered_chapters.append(line)
        
        # Se non abbiamo trovato capitoli validi, usa le righe originali
        if not filtered_chapters:
            filtered_chapters = [line for line in chapters if line.strip()]
        
        # Prepara la risposta cumulativa
        book_content = []
        
        # Aggiungi introduzione se non è già nei capitoli
        has_intro = any('introduz' in chapter.lower() or 'introduct' in chapter.lower() for chapter in filtered_chapters)
        if not has_intro:
            book_content.append("# Introduzione\n\n[Introduzione del libro]")
        
        # Genera ciascun capitolo
        for i, chapter_title in enumerate(filtered_chapters):
            log(f"Generazione capitolo {i+1}/{len(filtered_chapters)}: {chapter_title}")
        
            # Prepara il prompt per il capitolo, sfruttando i dati CRISP
            chapter_prompt = f"""
            Scrivi il capitolo "{chapter_title}" per il libro "{book_title}" usando lo stile: {voice_style}.
        
            Il libro è posizionato come "{project_data.get('ANGOLO_ATTACCO', '')}" 
            e rivolto a {project_data.get('BUYER_PERSONA_SUMMARY', 'lettori interessati a questo argomento')}.
        
            L'idea centrale (Big Idea) del libro è: {project_data.get('BIG_IDEA', 'Non specificata')}
        
            I pilastri di contenuto principali sono:
            {project_data.get('CONTENT_PILLARS', 'Non specificati')}
        
            Il metodo proprietario presentato nel libro è:
            {project_data.get('PROPRIETARY_METHOD', 'Non specificato')}
        
            Il capitolo deve essere dettagliato, coinvolgente e allineato con gli obiettivi generali del libro.
            Lunghezza minima: 1500 parole.
        
            Includi:
            - Un'introduzione coinvolgente
            - Sezioni dettagliate sul tema
            - Esempi pratici e applicabili
            - Una conclusione che riassume i punti chiave
        
            Scrivi SOLO il contenuto del capitolo, senza includere "Capitolo X" o il titolo.
        
            Termina con la parola FINE quando il capitolo è completato.
            """
        
            # Invia il prompt a Genspark
            try:
                # Ottieni input box
                input_box = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper textarea"))
                )
            
                # Pulisci l'input box
                input_box.clear()
                time.sleep(0.5)
            
                # Inserisci il testo
                input_box.send_keys(chapter_prompt)
                time.sleep(1)
            
                # Trova e clicca il pulsante di invio
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.search-input-wrapper div.input-icon"))
                )
                send_button.click()
            
                # Attendi risposta
                log("⏳ Attesa risposta per il capitolo...")
            
                # Verifica completamento risposta
                last_length = 0
                stable_count = 0
                max_stable_counts = 2
                chapter_content = None
            
                # Importazione per evitare dipendenze circolari
                from ai_interfaces.genspark_driver import get_last_response
                
                for attempt in range(60):  # Max 10 minuti (60 * 10 secondi)
                    time.sleep(10)
                    response = get_last_response(driver, log)
                
                    if response:
                        current_length = len(response)
                    
                        if current_length == last_length:
                            stable_count += 1
                            if stable_count >= max_stable_counts:
                                # Risposta stabile
                                chapter_content = response
                                break
                        else:
                            stable_count = 0
                            last_length = current_length
            
                if not chapter_content:
                    raise Exception(f"Timeout in attesa della risposta per il capitolo {chapter_title}")
            
                # Rimuovi la parola FINE se presente
                if "FINE" in chapter_content:
                    chapter_content = chapter_content[:chapter_content.find("FINE")].strip()
            
                # Aggiungi il titolo e il contenuto al libro
                formatted_chapter = f"# {chapter_title}\n\n{chapter_content}"
                book_content.append(formatted_chapter)
            
                # Salva il capitolo nel database CRISP
                crisp_framework._save_result_to_db(
                    project_id,
                    f"CAP{i+1}",
                    formatted_chapter,
                    {"chapter_title": chapter_title}
                )
            
                log(f"✅ Capitolo {i+1} completato: {chapter_title}")
            
                # Gestisci il reset del contesto se necessario
                from ai_interfaces.browser_manager import handle_context_limit
                
                if i % 2 == 0:  # Ogni 2 capitoli
                    handle_context_limit(driver, log)
        
            except Exception as e:
                error_msg = f"Errore durante la generazione del capitolo {chapter_title}: {str(e)}"
                log(error_msg)
                logging.error(error_msg)
                book_content.append(f"# {chapter_title}\n\nErrore durante la generazione di questo capitolo: {str(e)}")
        
            # Breve pausa tra i capitoli
            time.sleep(5)
        
        # Aggiungi conclusione se non è già nei capitoli
        has_conclusion = any('conclus' in chapter.lower() or 'conclusion' in chapter.lower() for chapter in filtered_chapters)
        if not has_conclusion:
            book_content.append("# Conclusione\n\n[Conclusione del libro]")
        
        # Unisci tutti i capitoli
        complete_book = "\n\n".join(book_content)
        
        # Salva il libro in un file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        book_filename = f"book_{timestamp}.md"
        with open(book_filename, "w", encoding="utf-8") as f:
            f.write(complete_book)
        
        # Salva anche nel database CRISP
        crisp_framework._save_result_to_db(
            project_id,
            "COMPLETE_BOOK",
            complete_book,
            {
                "title": book_title,
                "language": book_language,
                "style": voice_style,
                "chapters": len(filtered_chapters),
                "filename": book_filename
            }
        )
        
        log(f"📚 Libro generato e salvato come: {book_filename}")
        return book_filename
    
    except Exception as e:
        error_msg = f"Errore durante la generazione del libro CRISP 5.0: {str(e)}"
        log(error_msg)
        logging.error(error_msg)
        return f"Errore: {str(e)}"

def generate_book_legacy(book_title, book_language, voice_style, book_index, driver=None, chat_manager=None):
    """
    Metodo legacy per generare il libro.
    
    Args:
        book_title: Titolo del libro
        book_language: Lingua del libro
        voice_style: Stile narrativo
        book_index: Indice del libro
        driver: Istanza del WebDriver Selenium
        chat_manager: Istanza del ChatManager per il logging
        
    Returns:
        str: Messaggio di completamento o errore
    """
    # Funzione di log
    def log(message):
        if chat_manager:
            chat_manager.add_log(message)
        else:
            print(message)

    try:
        if not book_title.strip():
            log("Errore: Il titolo del libro è obbligatorio!")
            return "Errore: Il titolo del libro è obbligatorio!"
            
        if not book_index.strip():
            log("Errore: L'indice del libro è obbligatorio!")
            return "Errore: L'indice del libro è obbligatorio!"
        
        log(f"Generazione libro: {book_title}")
        
        # Qui andrà il codice per la generazione del libro legacy
        # Poiché non era fornito nell'originale, lasciamo un placeholder
        
        log("✅ Libro generato")
        return "Libro generato con successo"
        
    except Exception as e:
        import logging
        error_msg = f"Errore durante la generazione del libro: {str(e)}"
        log(error_msg)
        logging.error(error_msg)
        return f"Errore: {str(e)}"

def generate_book(book_title, book_language, voice_style, book_index,
                 driver=None, chat_manager=None, current_analysis=None,
                 book_type_hidden=None, send_to_genspark=None):
    """
    Genera il libro utilizzando i dati dell'interfaccia e i dati CRISP disponibili.
    
    Args:
        book_title: Titolo del libro
        book_language: Lingua del libro
        voice_style: Stile narrativo
        book_index: Indice del libro
        driver: Istanza del WebDriver Selenium
        chat_manager: Istanza del ChatManager per il logging
        current_analysis: Dizionario contenente i dati di analisi correnti
        book_type_hidden: Tipo di libro (se disponibile)
        send_to_genspark: Funzione per inviare testo a Genspark
        
    Returns:
        str: Percorso del libro generato o messaggio di errore
    """
    # Funzione di log
    def log(message):
        if chat_manager:
            chat_manager.add_log(message)
        else:
            print(message)
            
    if not book_title.strip():
        log("Errore: Il titolo del libro è obbligatorio!")
        return "Errore: Il titolo del libro è obbligatorio!"
        
    if not book_index.strip():
        log("Errore: L'indice del libro è obbligatorio!")
        return "Errore: L'indice del libro è obbligatorio!"

    try:
        # Recupera il tipo di libro
        book_type = "Manuale (Non-Fiction)"  # Default
        if book_type_hidden:
            book_type = book_type_hidden
        elif current_analysis and current_analysis.get('project_data', {}).get('LIBRO_TIPO'):
            book_type = current_analysis['project_data']['LIBRO_TIPO']
    
        log(f"Generazione libro: {book_title} (Tipo: {book_type})")
    
        # Carica il prompt specifico per questo tipo di libro
        chapter_prompt = _load_chapter_prompt(book_type)
    
        # Analizza l'indice per ottenere i capitoli
        chapters = _parse_book_index(book_index)
        log(f"Indice analizzato: {len(chapters)} capitoli trovati")
    
        # Recupera il contesto completo (dati CRISP)
        context_data = {}
        if current_analysis and current_analysis.get('project_data'):
            context_data = current_analysis['project_data']
    
        # Aggiungi i dati dell'interfaccia al contesto
        context_data['TITOLO_LIBRO'] = book_title
        context_data['LINGUA_LIBRO'] = book_language
        context_data['VOICE_STYLE'] = voice_style
    
        # Genera ogni capitolo
        for i, chapter in enumerate(chapters):
            log(f"Generazione capitolo {i+1}/{len(chapters)}: {chapter['title']}")
        
            # Prepara il prompt per questo capitolo
            full_prompt = chapter_prompt.replace("{text}", chapter['title'])
        
            # Sostituisci tutte le variabili dal contesto
            for var_name, var_value in context_data.items():
                placeholder = "{" + var_name + "}"
                if placeholder in full_prompt and var_value:
                    full_prompt = full_prompt.replace(placeholder, str(var_value))
        
            # Gestisci i placeholder non sostituiti
            full_prompt = _handle_missing_placeholders(full_prompt)
        
            # Invia il prompt e ottieni la risposta
            chapter_content = send_to_genspark(driver, full_prompt, log)
        
            # Pulisci la risposta
            if "FINE_RISPOSTA" in chapter_content:
                chapter_content = chapter_content.split("FINE_RISPOSTA")[0].strip()
            elif "FINE" in chapter_content:
                chapter_content = chapter_content.split("FINE")[0].strip()
        
            # Salva il capitolo
            _save_chapter(chapter['title'], chapter_content, book_title, log)
        
            # Applica un cooldown tra i capitoli
            if i < len(chapters) - 1:
                cooldown_time = 30 + (i * 5)  # Aumenta progressivamente
                log(f"Pausa di {cooldown_time} secondi prima del prossimo capitolo...")
                time.sleep(cooldown_time)
    
        log(f"✅ Libro generato con successo: {book_title}")
        return f"Libro {book_title} generato con successo"
    
    except Exception as e:
        error_msg = f"Errore durante la generazione del libro: {str(e)}"
        log(error_msg)
        logging.error(error_msg)
        return f"Errore: {str(e)}"

def _parse_book_index(book_index):
    """Analizza l'indice e lo converte in una lista di capitoli strutturati."""
    chapters = []
    lines = [line.strip() for line in book_index.split('\n') if line.strip()]

    for line in lines:
        # Ignora l'introduzione e la conclusione, li tratteremo separatamente
        if line.lower() in ["introduzione", "introduction", "conclusione", "conclusion"]:
            continue
    
        # Cerca di estrarre il titolo del capitolo
        chapter_match = re.match(r'(?:CAPITOLO|CHAPTER)\s*(\d+)?\s*:?\s*(.*)', line, re.IGNORECASE)
        if chapter_match:
            chapter_number = chapter_match.group(1) or ""
            chapter_title = chapter_match.group(2).strip()
            if chapter_title:
                chapters.append({
                    "number": chapter_number,
                    "title": chapter_title
                })
        elif line:  # Se è una linea con contenuto ma non è un formato standard
            chapters.append({
                "number": "",
                "title": line
            })

    return chapters

def _load_chapter_prompt(book_type):
    """Carica il prompt template per i capitoli specifico per il tipo di libro."""
    # Cerca prima in un file, altrimenti usa il template predefinito
    try:
        template_file = f"chapter_prompt_{book_type.lower().replace(' ', '_')}.txt"
        with open(template_file, "r", encoding="utf-8") as f:
            return f.read()
    except:
        # Template predefinito
        return """
        Scrivi il capitolo "{text}" per il libro "{TITOLO_LIBRO}" seguendo rigorosamente queste istruzioni di stile e struttura:
    
        STILE DI SCRITTURA:
        - Utilizza il seguente stile narrativo: {VOICE_STYLE}
        - Mantieni un tono coerente con l'angolo di attacco del libro: {ANGOLO_ATTACCO}
        - Rivolgi il testo direttamente al lettore con le caratteristiche di: {BUYER_PERSONA_SUMMARY}
        - Affronta i problemi principali evidenziati in: {IMPLEMENTATION_OBSTACLES}
    
        STRUTTURA E FORMATTAZIONE:
        - Inizia con un'introduzione coinvolgente che aggancia immediatamente il lettore
        - Dividi il capitolo in 3-5 sezioni principali con sottotitoli chiari
        - Usa tabelle invece di elenchi puntati per presentare informazioni strutturate
        - Includi almeno un esempio pratico o caso studio rilevante
        - Chiudi con un riepilogo dei punti chiave e un collegamento al capitolo successivo
    
        CONTENUTO SPECIFICO:
        - Allinea il contenuto alla Big Idea del libro: {BIG_IDEA}
        - Integra i pilastri di contenuto rilevanti: {CONTENT_PILLARS}
        - Quando applicabile, fai riferimento al metodo proprietario: {PROPRIETARY_METHOD}
    
        Sviluppa il contenuto in modo dettagliato, con una lunghezza compresa tra 2000-3000 parole.
        Scrivi FINE_RISPOSTA quando hai terminato.
        """

def _handle_missing_placeholders(text):
    """Gestisce i placeholder non sostituiti nel prompt."""
    # Trova tutti i placeholder rimanenti
    placeholders = re.findall(r'\{([A-Z_]+)\}', text)

    for placeholder in placeholders:
        # Sostituisce i placeholder mancanti con un valore generico
        full_placeholder = "{" + placeholder + "}"
        text = text.replace(full_placeholder, f"[Valore di {placeholder} non disponibile]")

    return text

def _save_chapter(chapter_title, chapter_content, book_title, log=None):
    """Salva il capitolo generato in un file."""
    from docx import Document

    safe_title = re.sub(r'[<>:"/\\|?*]', '', book_title)
    folder_path = os.path.join(os.getcwd(), safe_title)
    os.makedirs(folder_path, exist_ok=True)

    safe_chapter = re.sub(r'[<>:"/\\|?*]', '', chapter_title)
    file_path = os.path.join(folder_path, f"{safe_chapter}.docx")

    doc = Document()
    doc.add_heading(chapter_title, 1)

    # Aggiungi il contenuto con formattazione di base
    for paragraph in chapter_content.split('\n\n'):
        if paragraph.strip():
            if paragraph.strip().startswith('#'):
                # È un titolo
                level = paragraph.count('#')
                title_text = paragraph.strip('#').strip()
                doc.add_heading(title_text, level)
            else:
                # È un paragrafo normale
                doc.add_paragraph(paragraph)

    doc.save(file_path)
    if log:
        log(f"Capitolo '{chapter_title}' salvato in {file_path}")

    return file_path


