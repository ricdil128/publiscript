"""
Modulo per la formattazione HTML dei risultati delle analisi e del contenuto.
"""

import os
import re
import traceback

def process_text(text):
    """
    Processa il testo con formattazione di base
    
    Args:
        text: Testo da processare
        
    Returns:
        str: Testo formattato in HTML
    """
    if not text:
        return "Nessun dato disponibile"
    
    # Sostituisci ** con tag bold
    if '**' in text:
        parts = text.split('**')
        result = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Testo normale
                result += part
            else:  # Testo in grassetto
                result += f"<strong>{part}</strong>"
        return result

    return text

def format_analysis_results_html(keyword, market, book_type, language, context=None, log_callback=None, save_to_file=True, analysis_type=None):
    """
    Formatta i risultati dell'analisi in HTML per una visualizzazione migliore.

    Args:
        keyword: Keyword analizzata
        market: Mercato target
        book_type: Tipo di libro
        language: Lingua dell'output
        context: Dati di contesto aggiuntivi (opzionale)
        log_callback: Funzione di callback per il logging (opzionale)
        save_to_file: Se True, salva l'output in un file HTML (default: True)
        analysis_type: Il tipo di analisi (CRISP o Legacy)

    Returns:
        str: HTML formattato con i risultati
    """
    # Import os localmente per evitare problemi di scope
    import os
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        log(f"🎨 Formattazione risultati in HTML (save_to_file={save_to_file})")
    
        # 1. Leggi il file di contesto
        context_file = "context.txt"
        context_content = ""
        if os.path.exists(context_file):
            with open(context_file, "r", encoding="utf-8") as f:
                context_content = f.read()
                log(f"✅ File contesto letto: {len(context_content)} caratteri")
        else:
            log("⚠️ File context.txt non trovato")
    
        # 2. Estrai le sezioni dell'analisi
        all_sections = []
        section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
        section_matches = re.findall(section_pattern, context_content, re.DOTALL)
    
        if section_matches:
            all_sections = [(title.strip(), content.strip()) for title, content in section_matches]
            log(f"✅ Estratte {len(all_sections)} sezioni totali dal contesto")
            
            # Filtra solo le sezioni pertinenti alla keyword corrente
            keyword_clean = keyword.strip().lower()
            filtered_sections = []
            for title, content in all_sections:
                if keyword_clean in title.lower():
                    filtered_sections.append((title, content))
            
            # Livello 1
            if filtered_sections:
                # Livello 2
                # Se abbiamo più di una sezione, prendiamo solo la più recente
                if len(filtered_sections) > 1:
                    # Livello 3
                    # Le sezioni contengono timestamp nel titolo, estraiamoli e ordiniamoli
                    sections_with_timestamps = []
                    for title, content in filtered_sections:
                        # Livello 4
                        # Cerca un timestamp nel formato YYYYMMDD_HHMMSS nel titolo
                        timestamp_match = re.search(r'(\d{8}_\d{6})', title)
                        if timestamp_match:
                            # Livello 5
                            timestamp = timestamp_match.group(1)
                            sections_with_timestamps.append((title, content, timestamp))
                        else:
                            # Livello 5
                            # Se non c'è un timestamp, metti una stringa vuota come timestamp
                            sections_with_timestamps.append((title, content, ""))
        
                    # Livello 3
                    # Ordina le sezioni per timestamp (più recente prima)
                    sorted_sections = sorted(sections_with_timestamps, key=lambda x: x[2], reverse=True)
        
                    # Livello 3
                    # Prendi solo la sezione più recente
                    sections = [(sorted_sections[0][0], sorted_sections[0][1])]
                    log(f"✅ Filtrate {len(filtered_sections)} sezioni relative a '{keyword}', usando solo la più recente ({sorted_sections[0][2]})")
                else:
                    # Livello 3
                    sections = filtered_sections
                    log(f"✅ Filtrata 1 sezione relativa a '{keyword}'")
            else:
                # Livello 2
                # Se non troviamo sezioni specifiche per questa keyword, prendiamo le ultime N sezioni
                # che probabilmente sono quelle più recenti
                sections = all_sections[-3:]  # Ultime 3 sezioni
                log(f"⚠️ Nessuna sezione trovata per '{keyword}', usando le ultime {len(sections)} sezioni")
    
                # Livello 2
                # Fallback: divide il testo per numeri progressivi
                number_pattern = r'(\d+\).*?)(?=\d+\)|$)'
                number_matches = re.findall(number_pattern, context_content, re.DOTALL)

                if number_matches:
                    # Livello 3
                    sections = [(f"Sezione {i+1}", content.strip()) for i, content in enumerate(number_matches)]
                    log(f"✅ Estratte {len(sections)} sezioni numeriche alternate")
                else:
                    # Livello 3
                    # Ultimo fallback: usa il testo completo come sezione unica
                    sections = [("Risultati completi", context_content)]
                    log("⚠️ Impossibile estrarre sezioni, usando contenuto completo")

        # 3. Estrai metadati chiave dal context dictionary se disponibile
        metadata_html = ""
        if context and isinstance(context, dict):
            # Estrai solo metadati selezionati
            important_metadata = [
                ('MARKET_INSIGHTS', 'Insight di Mercato'),
                ('BUYER_PERSONA_SUMMARY', 'Profilo Buyer Persona'),
                ('ANGOLO_ATTACCO', 'Angolo di Attacco'),
                ('PROMESSA_PRINCIPALE', 'Promessa Principale'),
                ('BIG_IDEA', 'Big Idea'),
                ('TITOLO_LIBRO', 'Titolo Proposto')
            ]
        
            metadata_items = []
            for key, label in important_metadata:
                if key in context and context[key]:
                    value = context[key]
                    # Limita lunghezza per non sovraccaricare la UI
                    if isinstance(value, str) and len(value) > 200:
                        value = value[:197] + "..."
                    metadata_items.append(f"<div class='metadata-item'><strong>{label}:</strong> {value}</div>")
        
            if metadata_items:
                metadata_html = f"""
                <div class="metadata-box">
                    <h3>Dati Chiave Estratti</h3>
                    {"".join(metadata_items)}
                </div>
                """
                log(f"✅ Generati metadati HTML con {len(metadata_items)} elementi")
    
        # 4. Costruisci l'HTML completo
        result_html = ""
    
        # 5. Aggiungi ciascuna sezione come card
        for title, content in sections:
            # Pulisci il titolo
            clean_title = re.sub(r'\d+\)\s*', '', title).strip()
            clean_title = clean_title.replace('**', '')  # Rimuovi markdown
    
            # Determina l'icona in base al titolo
            icon = "📊"  # Default
            if "concorrenti" in title.lower() or "top 3" in title.lower():
                icon = "🏆"
            elif "profittabilità" in title.lower():
                icon = "💰"
            elif "buyer persona" in title.lower():
                icon = "👤"
            elif "recensioni" in title.lower() or "gap" in title.lower():
                icon = "🔍"
            elif "angolo" in title.lower() or "usp" in title.lower():
                icon = "🎯"
            elif "titolo" in title.lower():
                icon = "📝"
            elif "indice" in title.lower():
                icon = "📑"
    
            # Formatta il contenuto
            formatted_content = process_text(content)
    
            # Aggiungi la card della sezione con una struttura HTML migliore
            result_html += f"""
            <section class="section">
                <h2 class="section-title">{icon} {clean_title}</h2>
                <div class="section-content">
                    {formatted_content}
                </div>
            </section>
            """
    
        # Aggiungi i metadati in cima
        result_html = metadata_html + result_html
    
        log("✅ HTML dei risultati generato con successo")
        
        # 7. Salva l'HTML su file se richiesto
        if save_to_file:
            log(f"💾 Salvataggio HTML per keyword {keyword} in file...")
            # Determina il tipo di analisi se non specificato
            if analysis_type is None:
                # Cerca di determinarlo dal contesto o dalle sezioni
                if context and isinstance(context, dict) and 'type' in context:
                    analysis_type = "CRISP" if "crisp" in str(context.get("type", "")).lower() else "Legacy"
                elif any("crisp" in section[0].lower() for section in sections):
                    analysis_type = "CRISP"
                else:
                    analysis_type = "Legacy"
    
            # Salva il file HTML con gestione degli errori
            try:
                file_path = save_analysis_to_html(result_html, keyword, market, book_type, language, analysis_type, log_callback)
                log(f"✅ HTML salvato con successo in: {file_path}")
            except Exception as save_error:
                log(f"❌ Errore nel salvataggio HTML: {str(save_error)}")
                import traceback
                log(f"Stack trace: {traceback.format_exc()}")
        
                # Tentativo di salvataggio di emergenza
                try:
                    from datetime import datetime
            
                    # Crea directory se non esiste
                    os.makedirs("output/analisi_html", exist_ok=True)
            
                    # Sanitizza la keyword per il nome file
                    safe_keyword = ''.join(c if c.isalnum() else '_' for c in keyword)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
                    # Crea il nome file
                    emergency_file_path = f"output/analisi_html/{safe_keyword}_{analysis_type}_{timestamp}_emergency.html"
            
                    # Salva in modalità di emergenza
                    with open(emergency_file_path, "w", encoding="utf-8") as f:
                        f.write(f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Analisi di Emergenza: {keyword}</title>
                            <meta charset="UTF-8">
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                                h1 {{ color: #c00; }}
                            </style>
                        </head>
                        <body>
                            <h1>Analisi di {keyword} (Salvataggio di emergenza)</h1>
                            {result_html}
                        </body>
                        </html>
                        """)
                    log(f"✅ HTML salvato in modalità emergenza in: {emergency_file_path}")
                except Exception as emergency_error:
                    log(f"❌ Anche il salvataggio di emergenza è fallito: {str(emergency_error)}")

        # Verifica se ci sono duplicazioni nel codice HTML generato
        if "<body>" in result_html.lower() and result_html.lower().count("<body>") > 1:
            log("⚠️ Rilevata duplicazione nel codice HTML, tentativo di correzione")
            # Rimuovi tutto ciò che precede il primo <body>
            body_parts = re.split(r'<body[^>]*>', result_html, flags=re.IGNORECASE)
            if len(body_parts) > 1:
                # Mantieni solo la prima parte dopo <body>
                corrected_html = body_parts[1]
                # Se ci sono più </body>, prendi solo fino al primo
                if "</body>" in corrected_html.lower():
                    corrected_html = re.split(r'</body>', corrected_html, flags=re.IGNORECASE)[0]
                # Ricostruisci il risultato
                result_html = corrected_html
                log("✅ Rimosse duplicazioni nel codice HTML")

        # Aggiungi controllo per HTML vuoto
        if not "<div class=" in result_html and not "<section class=" in result_html:
            log("⚠️ HTML generato sembra essere vuoto o incompleto, aggiunta contenuti minimi")
    
            # Aggiungi almeno un contenuto minimo
            result_html += f"""
            <section class="section">
                <h2 class="section-title">📊 Analisi di {keyword}</h2>
                <div class="section-content">
                    <p>L'analisi è stata completata ma potrebbe richiedere un reload della pagina per visualizzare tutti i contenuti.</p>
                    <p><strong>Keyword:</strong> {keyword}</p>
                    <p><strong>Mercato:</strong> {market}</p>
                    <p><strong>Tipo:</strong> {book_type}</p>
                </div>
            </section>
            """

        return result_html

    except Exception as e:
        import traceback
        error_html = f"""
        <div class="error">
            <h2>Errore nella formattazione dei risultati</h2>
            <p>{str(e)}</p>
            <p>I dati sono stati salvati ma non possono essere visualizzati correttamente.</p>
        </div>
        """
        if log_callback:
            log_callback(f"❌ Errore nella formattazione HTML: {str(e)}")
            log_callback(traceback.format_exc())
        else:
            print(f"❌ Errore nella formattazione HTML: {str(e)}")
            print(traceback.format_exc())
        return error_html

def save_analysis_to_html(formatted_html, keyword, market, book_type, language, analysis_type="Legacy", log_callback=None):
    """
    Salva l'analisi formattata in un file HTML con design accattivante.
    Crea sia un file con timestamp che un file sempre aggiornato per ogni keyword.
    
    Args:
        formatted_html: L'HTML già formattato
        keyword: La keyword dell'analisi
        market: Il mercato di riferimento
        book_type: Il tipo di libro
        language: La lingua dell'analisi
        analysis_type: Il tipo di analisi (CRISP o Legacy)
        log_callback: Funzione per logging (opzionale)
        
    Returns:
        str: Percorso del file salvato
    """
    import os
    from datetime import datetime
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    # Crea directory di output se non esiste
    output_dir = "output/analisi_html"
    os.makedirs(output_dir, exist_ok=True)
    
    # Crea un nome file basato sulla keyword e sulla data
    safe_keyword = ''.join(c if c.isalnum() else '_' for c in keyword)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Due file: uno con timestamp (archivio storico) e uno sempre aggiornato (corrente)
    html_filename_timestamp = f"{output_dir}/{safe_keyword}_{analysis_type}_{timestamp}.html"
    html_filename_current = f"{output_dir}/{safe_keyword}_{analysis_type}_current.html"
    
    # Migliora la formattazione dell'HTML per renderla più leggibile
    # Aggiungiamo più struttura e semantica HTML corretta
    formatted_html = formatted_html.replace('<section class="section">', '\n<section class="section">\n')
    formatted_html = formatted_html.replace('</section>', '\n</section>\n')
    formatted_html = formatted_html.replace('<h2 class="section-title">', '\n  <h2 class="section-title">')
    formatted_html = formatted_html.replace('</h2>', '</h2>\n')
    formatted_html = formatted_html.replace('<div class="section-content">', '\n  <div class="section-content">\n')
    formatted_html = formatted_html.replace('</div>', '\n  </div>\n')
    formatted_html = formatted_html.replace('<p>', '\n    <p>')
    formatted_html = formatted_html.replace('</p>', '</p>\n')
    

    # Verifica se ci sono duplicazioni nel codice HTML
    if "<body>" in formatted_html.lower() and formatted_html.lower().count("<body>") > 1:
        log("⚠️ Rilevata duplicazione nel codice HTML, tentativo di correzione")
        # Rimuovi i tag body duplicati
        formatted_html = re.sub(r'<body[^>]*>.*?<body[^>]*>', '<body>', formatted_html, flags=re.IGNORECASE | re.DOTALL)
        # Rimuovi i tag /body duplicati
        formatted_html = re.sub(r'</body>.*?</body>', '</body>', formatted_html, flags=re.IGNORECASE | re.DOTALL)
        log("✅ Duplicazioni rimosse dal codice HTML")

    # Verifica se l'HTML è vuoto o manca di contenuto significativo
    if formatted_html.strip() == "" or (
       "<section" not in formatted_html.lower() and 
       "<div" not in formatted_html.lower()):
        log("⚠️ HTML formattato vuoto o privo di contenuto significativo")
        # Aggiungi un contenuto minimo
        formatted_html = f"""
        <section class="section">
            <h2 class="section-title">📊 Analisi {analysis_type} per {keyword}</h2>
            <div class="section-content">
                <p>L'analisi è stata completata ma potrebbe richiedere il caricamento 
                   dei dati dal contesto. Si consiglia di riprovare l'analisi se
                   questo messaggio persiste.</p>
            </div>
        </section>
        """
        log("✅ Aggiunto contenuto HTML minimo")


    # Aggiungi stili CSS per un design accattivante
    styled_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi {analysis_type}: {keyword} - {market}</title>
    <style>
        :root {{
            --primary-color: #3f51b5;
            --secondary-color: #ff4081;
            --light-bg: #f5f5f5;
            --dark-bg: #333;
            --text-color: #212121;
            --light-text: #f5f5f5;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            margin: 0;
            padding: 0;
            background-color: var(--light-bg);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background-color: var(--primary-color);
            color: var(--light-text);
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            font-weight: 600;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        h2 {{
            font-size: 1.8rem;
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 5px;
            margin-top: 40px;
        }}
        h3 {{
            font-size: 1.4rem;
            color: var(--secondary-color);
            margin-top: 30px;
        }}
        .section {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            padding: 25px;
        }}
        .section-title {{
            font-size: 1.4rem;
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        /* NUOVO: Rimuovi white-space: pre-line per consentire una formattazione più avanzata */
        .section-content {{
            white-space: normal;
            line-height: 1.8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
        }}
        th {{
            background-color: var(--primary-color);
            color: white;
            text-align: left;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 15px;
            border-left: 5px solid #ffc107;
            margin: 20px 0;
        }}
        .meta-info {{
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 15px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        footer {{
            background-color: var(--dark-bg);
            color: var(--light-text);
            text-align: center;
            padding: 15px;
            margin-top: 30px;
            border-radius: 0 0 8px 8px;
        }}
        ul, ol {{
            margin-top: 15px;
            margin-bottom: 15px;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 10px;
            line-height: 1.5;
        }}
        /* NUOVO: Stili specifici per liste puntate e numerate */
        .section-content ul li {{
            list-style-type: disc;
        }}
        .section-content ol li {{
            list-style-type: decimal;
        }}
        /* NUOVO: Miglioramento per i titoli interni alle sezioni */
        .section-content h3 {{
            margin-top: 25px;
            margin-bottom: 15px;
            color: #3f51b5;
            font-size: 1.3rem;
        }}
        /* NUOVO: Miglioramento paragrafi */
        .section-content p {{
            margin-bottom: 15px;
            line-height: 1.6;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            margin-right: 5px;
            background-color: #e0e0e0;
            border-radius: 5px;
            font-size: 0.9rem;
        }}
        .section-card {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            padding: 20px;
            transition: all 0.2s ease;
        }}
        .section-card:hover {{
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .metadata-box {{
            background-color: #e8f0fe;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 25px;
        }}
        .metadata-item {{
            margin-bottom: 8px;
        }}
        pre {{
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        blockquote {{
            border-left: 5px solid #ddd;
            padding-left: 15px;
            margin-left: 0;
            font-style: italic;
            color: #555;
        }}
        /* NUOVO: Stile specifico per il buyer persona */
        .buyer-persona {{
            background-color: #f9f9ff;
            border-left: 4px solid #3f51b5;
            padding: 15px;
            margin-bottom: 20px;
        }}
        /* NUOVO: Stile per evidenziare le sezioni principali */
        .main-section {{
            background-color: #f0f8ff;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Analisi {analysis_type}: {keyword}</h1>
            <div class="meta-info">
                <strong>Mercato:</strong> {market} | 
                <strong>Tipo:</strong> {book_type} | 
                <strong>Lingua:</strong> {language} | 
                <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </header>
        
        <div class="content">
            {formatted_html}
        </div>
        
        <footer>
            <p>Generato da PubliScript {datetime.now().year} - {timestamp}</p>
        </footer>
    </div>
</body>
</html>
    """
    
    # Salva entrambe le versioni del file HTML
    try:
        # Salva la versione con timestamp (archivio storico)
        with open(html_filename_timestamp, "w", encoding="utf-8") as f:
            f.write(styled_html)
        
        # Salva la versione corrente (sempre aggiornata, sovrascrive ogni volta)
        with open(html_filename_current, "w", encoding="utf-8") as f:
            f.write(styled_html)
        
        log(f"✅ Report HTML salvato in: {os.path.abspath(html_filename_timestamp)}")
        log(f"✅ Report HTML aggiornato anche in: {os.path.abspath(html_filename_current)}")
        
        # Opzionalmente, apri il file nel browser
        import webbrowser
        try:
            # Apri la versione corrente (sempre aggiornata)
            webbrowser.open(f"file:///{os.path.abspath(html_filename_current)}")
            log(f"✅ Report HTML aperto nel browser")
        except Exception as e:
            log(f"⚠️ Non è stato possibile aprire il file nel browser: {str(e)}")
        
        return html_filename_current  # Restituisce il percorso del file corrente
    except Exception as e:
        log(f"❌ Errore nel salvataggio del file HTML: {str(e)}")
        return None

def process_text(text):
    """
    Processa il testo con formattazione avanzata per una migliore leggibilità
    
    Args:
        text: Testo da processare
        
    Returns:
        str: Testo formattato in HTML
    """
    import re
    
    if not text:
        return "Nessun dato disponibile"
    
    # Prepara il testo per i punti elenco
    # Converti punti elenco
    text = re.sub(r'(?m)^[-*•]\s*(.*?)$', r'<li>\1</li>', text)
    
    # Trova gruppi di <li> e racchiudili in <ul>
    parts = []
    in_list = False
    for line in text.split('\n'):
        if line.strip().startswith('<li>'):
            if not in_list:
                parts.append('<ul>')
                in_list = True
            parts.append(line)
        else:
            if in_list:
                parts.append('</ul>')
                in_list = False
            parts.append(line)
    
    if in_list:
        parts.append('</ul>')
    
    text = '\n'.join(parts)
    
    # Converti elementi numerati
    text = re.sub(r'(?m)^\d+\.\s+(.*?)$', r'<li>\1</li>', text)
    
    # Trova gruppi di <li> numerati e racchiudili in <ol>
    parts = []
    in_list = False
    for line in text.split('\n'):
        if line.strip().startswith('<li>') and not line.strip().startswith('<ul>'):
            if not in_list:
                parts.append('<ol>')
                in_list = True
            parts.append(line)
        else:
            if in_list:
                parts.append('</ol>')
                in_list = False
            parts.append(line)
    
    if in_list:
        parts.append('</ol>')
    
    text = '\n'.join(parts)
    
    # Converti intestazioni
    headers = ['PROFILO DEMOGRAFICO', 'BACKGROUND DI SALUTE', 'OBIETTIVI', 'PROBLEMI', 
               'LIVELLO DI CONSAPEVOLEZZA', 'BUYER PERSONA']
    
    for header in headers:
        text = re.sub(rf'(?m)^{header}[:]*\s*$', f'<h3>{header}</h3>', text, flags=re.IGNORECASE)
    
    # Converti paragrafi (linee che non sono già HTML)
    lines = text.split('\n')
    formatted_lines = []
    current_paragraph = []
    
    for line in lines:
        if line.strip() == '':
            # Linea vuota: termina il paragrafo corrente se esiste
            if current_paragraph:
                paragraph_text = ' '.join(current_paragraph)
                # Evita di avvolgere in <p> se già contiene HTML
                if not any(tag in paragraph_text for tag in ['<h3>', '<ul>', '<ol>', '<li>']):
                    formatted_lines.append(f'<p>{paragraph_text}</p>')
                else:
                    formatted_lines.append(paragraph_text)
                current_paragraph = []
            formatted_lines.append('')  # mantiene la linea vuota
        elif line.strip().startswith(('<h3>', '<ul>', '<ol>', '<li>', '<p>')):
            # Se è già un tag HTML, termina il paragrafo corrente e aggiungi la riga
            if current_paragraph:
                formatted_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
                current_paragraph = []
            formatted_lines.append(line)
        else:
            # Accumula le righe in un paragrafo
            current_paragraph.append(line.strip())
    
    # Aggiungi l'ultimo paragrafo se ne esiste uno
    if current_paragraph:
        formatted_lines.append(f'<p>{" ".join(current_paragraph)}</p>')
    
    text = '\n'.join(formatted_lines)
    
    # Gestisci formattazione in grassetto
    if '**' in text:
        parts = text.split('**')
        result = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Testo normale
                result += part
            else:  # Testo in grassetto
                result += f"<strong>{part}</strong>"
        text = result
    
    # Formattazioni finali (aggiunta di classi speciali)
    if 'BUYER PERSONA' in text:
        text = text.replace('<h3>BUYER PERSONA</h3>', '<div class="buyer-persona"><h3>BUYER PERSONA</h3>')
        text = text + '</div>'
    
    return text
def process_list_html(content, list_type):
    """
    Formatta una lista in HTML
    
    Args:
        content: Contenuto della lista
        list_type: Tipo di lista (REVIEW_INSIGHTS, IMPLEMENTATION_OBSTACLES, MARKET_GAPS, ecc.)
        
    Returns:
        str: Lista formattata in HTML
    """
    if not content:
        return "Nessun elemento disponibile"

    # Estrai elementi della lista
    items = []
    current_item = ""

    # Dividi per righe e cerca elementi numerati o con trattino
    for line in content.strip().split('\n'):
        line = line.strip()
        if line.startswith('- ') or re.match(r'^\d+\.', line):
            if current_item:
                items.append(current_item)
            # Rimuovi il prefisso (- o numero.)
            if line.startswith('- '):
                current_item = line[2:]
            else:
                # Trova la posizione del punto
                dot_pos = line.find('.')
                if dot_pos > 0:
                    current_item = line[dot_pos + 1:].strip()
        elif line:
            if current_item:
                current_item += " " + line
            else:
                current_item = line

    if current_item:
        items.append(current_item)

    if not items:
        return f"{process_text(content)}"

    # Definisci classi CSS in base al tipo
    bg_class = ""
    if list_type == "REVIEW_INSIGHTS":
        bg_class = "bg-red-50"
    elif list_type == "IMPLEMENTATION_OBSTACLES":
        bg_class = "bg-yellow-50"
    elif list_type == "MARKET_GAPS":
        bg_class = "bg-green-50"

    # Crea la lista HTML
    html = ''
    for i, item in enumerate(items):
        html += f"""
        
            {i+1}
            
                {process_text(item)}
            
        
        """
    html += ''

    return html

def process_patterns_html(content, pattern_type):
    """
    Formatta pattern di titoli o strutture in HTML
    
    Args:
        content: Contenuto del pattern
        pattern_type: Tipo di pattern (TITLE_PATTERNS, STRUCTURE_PATTERNS, ecc.)
        
    Returns:
        str: Pattern formattato in HTML
    """
    if not content:
        return "Nessun pattern disponibile"

    # Semplice controllo per tabelle
    if content.strip().startswith('|') and content.strip().endswith('|'):
        return process_table_html(content)

    # Estrai pattern
    patterns = []
    current_pattern = ""

    for line in content.strip().split('\n'):
        line = line.strip()
        if line.startswith('- ') or re.match(r'^\d+\.', line):
            if current_pattern:
                patterns.append(current_pattern)
            # Rimuovi il prefisso (- o numero.)
            if line.startswith('- '):
                current_pattern = line[2:]
            else:
                # Trova la posizione del punto
                dot_pos = line.find('.')
                if dot_pos > 0:
                    current_pattern = line[dot_pos + 1:].strip()
        elif line:
            if current_pattern:
                current_pattern += " " + line
            else:
                current_pattern = line

    if current_pattern:
        patterns.append(current_pattern)

    if not patterns:
        return f"{process_text(content)}"

    # Crea layout appropriato in base al tipo
    if pattern_type == "TITLE_PATTERNS":
        html = ''
        for i, pattern in enumerate(patterns):
            # Dividi il pattern in titolo e esempio
            parts = pattern.split(' - ', 1)
            title = parts[0].strip()
            example = parts[1].strip() if len(parts) > 1 else ""
        
            html += f"""
            
                Pattern {i+1}
                {process_text(title)}
                Es: {process_text(example)}
            
            """
        html += ''
    else:  # STRUCTURE_PATTERNS
        html = ''
        for i, pattern in enumerate(patterns):
            # Dividi in titolo e descrizione
            parts = pattern.split(':', 1)
            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""
        
            html += f"""
            
                {process_text(title)}
                {process_text(description)}
            
            """
        html += ''

    return html

def process_table_html(content):
    """
    Converte una tabella in formato markdown in HTML
    
    Args:
        content: Contenuto della tabella in formato markdown
        
    Returns:
        str: Tabella formattata in HTML
    """
    if not content or '|' not in content:
        return f"{process_text(content)}"

    # Dividi le righe
    rows = content.strip().split('\n')

    # Se non abbiamo almeno 2 righe (intestazione + separatore), non è una tabella valida
    if len(rows) < 2:
        return f"{process_text(content)}"

    html = ''

    # Processa intestazione
    header_cells = [cell.strip() for cell in rows[0].strip('|').split('|')]

    html += ''
    for cell in header_cells:
        html += f''
    html += ''

    # Salta l'intestazione e il separatore
    for row in rows[2:]:
        if '---' in row:  # Ignora eventuali altri separatori
            continue
        
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        html += ''
        for cell in cells:
            html += f''
        html += ''

    html += '{process_text(cell)}{process_text(cell)}'
    return html

def save_analysis_to_html(formatted_html, keyword, market, book_type, language, analysis_type="Legacy", log_callback=None):
    """
    Salva l'analisi formattata in file HTML con design accattivante.
    Crea sia un file con timestamp che un file sempre aggiornato per ogni keyword.
    
    Args:
        formatted_html: L'HTML già formattato
        keyword: La keyword dell'analisi
        market: Il mercato di riferimento
        book_type: Il tipo di libro
        language: La lingua dell'analisi
        analysis_type: Il tipo di analisi (CRISP o Legacy)
        log_callback: Funzione per logging (opzionale)
        
    Returns:
        str: Percorso del file salvato
    """
    import os
    from datetime import datetime
    
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    # Crea directory di output se non esiste
    output_dir = "output/analisi_html"
    os.makedirs(output_dir, exist_ok=True)
    
    # Crea un nome file basato sulla keyword e sulla data
    safe_keyword = ''.join(c if c.isalnum() else '_' for c in keyword)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Due file: uno con timestamp (storico) e uno sempre aggiornato (corrente)
    html_filename_timestamp = f"{output_dir}/{safe_keyword}_{analysis_type}_{timestamp}.html"
    html_filename_current = f"{output_dir}/{safe_keyword}_{analysis_type}_current.html"
    
    # Aggiungi stili CSS per un design accattivante
    styled_html = f"""
    
    
    
        
        
        Analisi {analysis_type}: {keyword} - {market}
        
            :root {{
                --primary-color: #3f51b5;
                --secondary-color: #ff4081;
                --light-bg: #f5f5f5;
                --dark-bg: #333;
                --text-color: #212121;
                --light-text: #f5f5f5;
            }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: var(--text-color);
                margin: 0;
                padding: 0;
                background-color: var(--light-bg);
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            header {{
                background-color: var(--primary-color);
                color: var(--light-text);
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                font-weight: 600;
            }}
            h1 {{
                font-size: 2.5rem;
                margin-bottom: 10px;
            }}
            h2 {{
                font-size: 1.8rem;
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 5px;
                margin-top: 40px;
            }}
            h3 {{
                font-size: 1.4rem;
                color: var(--secondary-color);
                margin-top: 30px;
            }}
            .section {{
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                padding: 25px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
            }}
            th {{
                background-color: var(--primary-color);
                color: white;
                text-align: left;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .highlight {{
                background-color: #fff3cd;
                padding: 15px;
                border-left: 5px solid #ffc107;
                margin: 20px 0;
            }}
            .meta-info {{
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 15px;
            }}
            img {{
                max-width: 100%;
                height: auto;
                border-radius: 4px;
            }}
            footer {{
                background-color: var(--dark-bg);
                color: var(--light-text);
                text-align: center;
                padding: 15px;
                margin-top: 30px;
                border-radius: 0 0 8px 8px;
            }}
            ul, ol {{
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            li {{
                margin-bottom: 8px;
            }}
            .bestseller-item, .idea-item, .gap-item {{
                background-color: white;
                border-left: 5px solid var(--primary-color);
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 0 8px 8px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .pattern-item {{
                border-left: 5px solid var(--secondary-color);
            }}
            pre {{
                background-color: #f0f0f0;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                white-space: pre-wrap;
            }}
            blockquote {{
                border-left: 5px solid #ddd;
                padding-left: 15px;
                margin-left: 0;
                font-style: italic;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Analisi {analysis_type}: {keyword}</h1>
                <div class="meta-info">
                    <strong>Mercato:</strong> {market} | 
                    <strong>Tipo:</strong> {book_type} | 
                    <strong>Lingua:</strong> {language} | 
                    <strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                </div>
            </header>
            
            <!-- Contenuto dell'analisi -->
            <div class="section">
                {formatted_html}
            </div>
            
            <footer>
                <p>Generato da PubliScript {datetime.now().year} - {timestamp}</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # Salva entrambe le versioni del file HTML
    try:
        # Salva la versione con timestamp (archivio storico)
        with open(html_filename_timestamp, "w", encoding="utf-8") as f:
            f.write(styled_html)
        
        # Salva la versione corrente (sempre aggiornata, sovrascrive ogni volta)
        with open(html_filename_current, "w", encoding="utf-8") as f:
            f.write(styled_html)
        
        log(f"✅ Report HTML salvato in: {os.path.abspath(html_filename_timestamp)}")
        log(f"✅ Report HTML aggiornato anche in: {os.path.abspath(html_filename_current)}")
        
        # Opzionalmente, apri il file nel browser
        import webbrowser
        try:
            # Apri la versione corrente (sempre aggiornata)
            webbrowser.open(f"file:///{os.path.abspath(html_filename_current)}")
            log(f"✅ Report HTML aperto nel browser")
        except Exception as e:
            log(f"⚠️ Non è stato possibile aprire il file nel browser: {str(e)}")
        
        return html_filename_current  # Restituisce il percorso del file corrente
    except Exception as e:
        log(f"❌ Errore nel salvataggio del file HTML: {str(e)}")
        return None