"""
Modulo per la formattazione HTML dei risultati delle analisi e del contenuto.
"""

import os
import re
import traceback

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
        sections = []
        section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
        section_matches = re.findall(section_pattern, context_content, re.DOTALL)
    
        if section_matches:
            sections = [(title.strip(), content.strip()) for title, content in section_matches]
            log(f"✅ Estratte {len(sections)} sezioni dal contesto")
        else:
            # Fallback: divide il testo per numeri progressivi
            number_pattern = r'(\d+\).*?)(?=\d+\)|$)'
            number_matches = re.findall(number_pattern, context_content, re.DOTALL)
        
            if number_matches:
                sections = [(f"Sezione {i+1}", content.strip()) for i, content in enumerate(number_matches)]
                log(f"✅ Estratte {len(sections)} sezioni numeriche alternate")
            else:
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
                <div class="metadata-box bg-blue-50 p-4 rounded-lg mb-4">
                    <h3 class="text-md font-bold mb-2 text-blue-800">Dati Chiave Estratti:</h3>
                    {"".join(metadata_items)}
                </div>
                """
                log(f"✅ Generati metadati HTML con {len(metadata_items)} elementi")
    
        # 4. Costruisci l'HTML completo
        result_html = f"""
        <div class="analysis-results">
            <div class="header bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-4 rounded-lg mb-4">
                <h2 class="text-xl font-bold">Analisi di Mercato: {keyword}</h2>
                <div class="flex flex-wrap gap-2 mt-2">
                    <div class="badge bg-blue-200 text-blue-800 px-2 py-1 rounded">Mercato: {market}</div>
                    <div class="badge bg-blue-200 text-blue-800 px-2 py-1 rounded">Tipo: {book_type}</div>
                    <div class="badge bg-blue-200 text-blue-800 px-2 py-1 rounded">Lingua: {language}</div>
                </div>
            </div>
    
            {metadata_html}
    
            <div class="results-container">
        """
    
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
        
            # Aggiungi la card della sezione
            result_html += f"""
            <div class="section-card bg-white p-4 rounded-lg shadow mb-4 hover:shadow-lg transition-shadow">
                <h3 class="text-lg font-bold mb-2 text-gray-800">{icon} {clean_title}</h3>
                <div class="content whitespace-pre-line text-gray-700">{process_text(content)}</div>
            </div>
            """
    
        # 6. Chiudi l'HTML
        result_html += """
            </div>
        </div>
        """
    
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
                        import os
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
                            </head>
                            <body>
                                <h1>Analisi di {keyword} (Salvataggio di emergenza)</h1>
                                <div>{result_html}</div>
                            </body>
                            </html>
                            """)
                        log(f"✅ HTML salvato in modalità emergenza in: {emergency_file_path}")
                    except Exception as emergency_error:
                        log(f"❌ Anche il salvataggio di emergenza è fallito: {str(emergency_error)}")
        
            return result_html

        except Exception as e:
            import traceback
            error_html = f"""
            <div class="error-message bg-red-50 border-l-4 border-red-500 p-4">
                <h3 class="text-red-700 font-bold">Errore nella formattazione dei risultati</h3>
                <p class="text-red-600">{str(e)}</p>
                <p class="text-gray-700 mt-2">I dati sono stati salvati ma non possono essere visualizzati correttamente.</p>
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
    
    html_filename = f"{output_dir}/{safe_keyword}_{analysis_type}_{timestamp}.html"
    
    # Aggiungi stili CSS per un design accattivante
    styled_html = f"""
    <!DOCTYPE html>
    <html lang="{language}">
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
    
    # Salva l'HTML su file
    try:
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(styled_html)
        
        log(f"✅ Report HTML salvato in: {os.path.abspath(html_filename)}")
        
        # Opzionalmente, apri il file nel browser
        import webbrowser
        try:
            webbrowser.open(f"file:///{os.path.abspath(html_filename)}")
            log(f"✅ Report HTML aperto nel browser")
        except Exception as e:
            log(f"⚠️ Non è stato possibile aprire il file nel browser: {str(e)}")
        
        return html_filename
    except Exception as e:
        log(f"❌ Errore nel salvataggio del file HTML: {str(e)}")
        return None

def process_text(text):
    """
    Processa il testo con formattazione di base
    
    Args:
        text: Testo da processare
        
    Returns:
        str: Testo formattato in HTML
    """
    if not text:
        return "<em class='text-gray-500'>Nessun dato disponibile</em>"
    
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
        return "<p>Nessun elemento disponibile</p>"

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
        return f"<p>{process_text(content)}</p>"

    # Definisci classi CSS in base al tipo
    bg_class = ""
    if list_type == "REVIEW_INSIGHTS":
        bg_class = "bg-red-50"
    elif list_type == "IMPLEMENTATION_OBSTACLES":
        bg_class = "bg-yellow-50"
    elif list_type == "MARKET_GAPS":
        bg_class = "bg-green-50"

    # Crea la lista HTML
    html = '<ul class="space-y-3">'
    for i, item in enumerate(items):
        html += f"""
        <li class="{bg_class} p-3 rounded-lg flex items-start">
            <div class="rounded-full bg-blue-100 text-blue-800 h-6 w-6 flex items-center justify-center mr-3 mt-1 flex-shrink-0">{i+1}</div>
            <div>
                <p class="font-medium">{process_text(item)}</p>
            </div>
        </li>
        """
    html += '</ul>'

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
        return "<p>Nessun pattern disponibile</p>"

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
        return f"<p>{process_text(content)}</p>"

    # Crea layout appropriato in base al tipo
    if pattern_type == "TITLE_PATTERNS":
        html = '<div class="space-y-3">'
        for i, pattern in enumerate(patterns):
            # Dividi il pattern in titolo e esempio
            parts = pattern.split(' - ', 1)
            title = parts[0].strip()
            example = parts[1].strip() if len(parts) > 1 else ""
        
            html += f"""
            <div class="bg-blue-50 p-3 rounded-lg">
                <span class="badge bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">Pattern {i+1}</span>
                <span class="font-semibold">{process_text(title)}</span>
                <p class="mt-1 text-gray-700">Es: <span class="italic">{process_text(example)}</span></p>
            </div>
            """
        html += '</div>'
    else:  # STRUCTURE_PATTERNS
        html = '<div class="grid grid-cols-2 gap-4">'
        for i, pattern in enumerate(patterns):
            # Dividi in titolo e descrizione
            parts = pattern.split(':', 1)
            title = parts[0].strip()
            description = parts[1].strip() if len(parts) > 1 else ""
        
            html += f"""
            <div class="bg-indigo-50 p-3 rounded-lg">
                <h4 class="font-semibold text-indigo-700">{process_text(title)}</h4>
                <p class="mt-2">{process_text(description)}</p>
            </div>
            """
        html += '</div>'

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
        return f"<p>{process_text(content)}</p>"

    # Dividi le righe
    rows = content.strip().split('\n')

    # Se non abbiamo almeno 2 righe (intestazione + separatore), non è una tabella valida
    if len(rows) < 2:
        return f"<p>{process_text(content)}</p>"

    html = '<div class="overflow-x-auto"><table class="data-table w-full">'

    # Processa intestazione
    header_cells = [cell.strip() for cell in rows[0].strip('|').split('|')]

    html += '<thead><tr>'
    for cell in header_cells:
        html += f'<th class="text-left py-2 px-4 bg-gray-50">{process_text(cell)}</th>'
    html += '</tr></thead><tbody>'

    # Salta l'intestazione e il separatore
    for row in rows[2:]:
        if '---' in row:  # Ignora eventuali altri separatori
            continue
        
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        html += '<tr>'
        for cell in cells:
            html += f'<td class="py-2 px-4 border-t">{process_text(cell)}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
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
    <!DOCTYPE html>
    <html lang="{language}">
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