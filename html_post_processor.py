"""
Script post-processore per HTML di PubliScript.
Monitora la directory output per nuovi file HTML e li riprocessa automaticamente.

Uso:
1. Esegui questo script in una finestra separata
2. Lo script rimarrà in esecuzione, monitorando le directory di output
3. Quando viene generato un nuovo file HTML, lo riprocesserà automaticamente

"""
import os
import re
import time
import sys
from datetime import datetime, timedelta
import webbrowser
import shutil

# Configurazioni
CHECK_INTERVAL = 5  # Controlla ogni 5 secondi
OUTPUT_DIRS = [
    os.path.join("output", "genspark_formatted"),
    os.path.join("output", "analisi_html")
]
BACKUP_DIR = os.path.join("output", "original_backups")
PROCESSED_LOG = os.path.join("output", "processed_files.log")

# Crea le directory se non esistono
for directory in OUTPUT_DIRS + [BACKUP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Carica il log dei file già processati
processed_files = set()
if os.path.exists(PROCESSED_LOG):
    with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
        processed_files = set(line.strip() for line in f.readlines())

def log_message(message):
    """Registra un messaggio con timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")
    
    # Scrivi anche su file
    with open(os.path.join("output", "post_processor.log"), 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

def format_html_file(file_path):
    """Formatta un file HTML esistente"""
    try:
        log_message(f"Elaborazione di {file_path}")
        
        # Leggi il contenuto del file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Estrai il titolo e altre informazioni dal nome file
        file_name = os.path.basename(file_path)
        parts = file_name.split('_')
        keyword = parts[0].replace('_', ' ') if parts else "Analisi"
        
        # Crea una copia di backup
        backup_path = os.path.join(BACKUP_DIR, f"orig_{file_name}")
        shutil.copy2(file_path, backup_path)
        log_message(f"Backup creato in {backup_path}")
        
        # Converti tabelle markdown in HTML
        def format_markdown_table(match):
            table_text = match.group(1)
            rows = [row.strip() for row in table_text.strip().split('\n')]
            if len(rows) < 2:
                return match.group(0)
            
            html_table = '<table class="data-table">\n'
            
            # Intestazione
            if '|' in rows[0]:
                header_cells = [cell.strip() for cell in rows[0].strip('|').split('|')]
                
                html_table += '  <thead>\n    <tr>\n'
                for cell in header_cells:
                    if cell.strip():
                        html_table += f'      <th>{cell}</th>\n'
                html_table += '    </tr>\n  </thead>\n'
            
            # Corpo della tabella (salta la riga di separazione)
            if len(rows) > 2:
                html_table += '  <tbody>\n'
                for row in rows[2:]:
                    if '---' in row or row.strip().startswith('|-'):
                        continue
                        
                    if '|' in row:
                        cells = [cell.strip() for cell in row.strip('|').split('|')]
                        
                        html_table += '    <tr>\n'
                        for cell in cells:
                            if cell.strip():
                                html_table += f'      <td>{cell}</td>\n'
                        html_table += '    </tr>\n'
                
                html_table += '  </tbody>\n'
            
            html_table += '</table>\n'
            return html_table
            
        # Pattern tabella markdown
        table_pattern = r'(\|[^\n]+\|\n\|[\-\|: ]+\|\n(?:\|[^\n]+\|\n)+)'
        
        # Cerca il contenuto del body esistente
        body_match = re.search(r'<body.*?>(.*?)</body>', content, re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
            log_message(f"Contenuto del body estratto: {len(body_content)} caratteri")
            
            # Formatta le tabelle nel body
            body_content = re.sub(table_pattern, format_markdown_table, body_content)
        else:
            log_message(f"Body non trovato, utilizzo contenuto completo")
            body_content = content
            
            # Formatta le tabelle nel contenuto completo
            body_content = re.sub(table_pattern, format_markdown_table, body_content)
            
        # Crea un nuovo file HTML con stili completi
        new_html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi: {keyword}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background-color: #3f51b5;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
            margin-bottom: 30px;
        }}
        h1, h2, h3 {{
            font-weight: 600;
        }}
        h1 {{
            font-size: 2.2rem;
            margin-bottom: 10px;
        }}
        h2 {{
            font-size: 1.8rem;
            color: #3f51b5;
            border-bottom: 2px solid #3f51b5;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        h3 {{
            font-size: 1.4rem;
            color: #ff4081;
            margin-top: 25px;
        }}
        .section {{
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        }}
        .section-title {{
            font-size: 1.5rem;
            color: #3f51b5;
            margin-top: 0;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 3px rgba(0,0,0,0.1);
        }}
        th, td {{
            text-align: left;
            padding: 12px 15px;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #3f51b5;
            color: white;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .content {{
            background-color: white;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        ul, ol {{
            padding-left: 20px;
            margin-bottom: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .highlight {{
            background-color: #fffde7;
            padding: 15px;
            border-left: 5px solid #ffd600;
            margin: 20px 0;
        }}
        .meta-info {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        footer {{
            text-align: center;
            padding: 15px;
            color: #666;
            font-size: 0.9rem;
            margin-top: 30px;
        }}
        .data-table {{
            width: 100%;
            margin: 20px 0;
            border-collapse: collapse;
        }}
        .data-table th {{
            background-color: #3f51b5;
            color: white;
            text-align: left;
            padding: 12px;
            font-weight: 600;
        }}
        .data-table td {{
            border: 1px solid #ddd;
            padding: 12px;
            vertical-align: top;
        }}
        .data-table tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Analisi: {keyword}</h1>
            <p>Post-processore attivo - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </header>
        
        <div class="content">
            {body_content}
        </div>
        
        <footer>
            <p>Auto-formattato da PubliScript Post-Processor {datetime.now().year}</p>
            <p style="font-size: 0.8em;">File originale: {file_name}</p>
        </footer>
    </div>
</body>
</html>"""
        
        # Scrivi il nuovo HTML
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
            
        # Aggiorna il log dei file processati
        with open(PROCESSED_LOG, 'a', encoding='utf-8') as f:
            f.write(f"{file_path}\n")
        processed_files.add(file_path)
        
        log_message(f"✅ File formattato con successo: {file_path}")
        return True
        
    except Exception as e:
        import traceback
        log_message(f"❌ Errore durante la formattazione: {str(e)}")
        log_message(traceback.format_exc())
        return False

def check_for_new_files():
    """Controlla se ci sono nuovi file HTML da processare"""
    new_files_found = False
    
    for output_dir in OUTPUT_DIRS:
        if not os.path.exists(output_dir):
            continue
            
        for file_name in os.listdir(output_dir):
            if file_name.endswith('.html'):
                file_path = os.path.join(output_dir, file_name)
                
                # Verifica se il file è stato modificato recentemente
                mod_time = os.path.getmtime(file_path)
                mod_date = datetime.fromtimestamp(mod_time)
                
                # Se il file è recente (ultimi 30 minuti) e non è già stato processato
                if datetime.now() - mod_date < timedelta(minutes=30) and file_path not in processed_files:
                    log_message(f"🔍 Trovato nuovo file HTML: {file_path}")
                    format_html_file(file_path)
                    new_files_found = True
    
    return new_files_found

def main():
    """Loop principale del post-processore"""
    log_message("🚀 Post-processore HTML avviato")
    log_message(f"📂 Monitoraggio delle directory: {', '.join(OUTPUT_DIRS)}")
    
    # Chiedi se processare i file esistenti
    if input("Processare anche i file HTML esistenti? (s/n): ").lower() == 's':
        log_message("🔄 Processamento dei file esistenti...")
        for output_dir in OUTPUT_DIRS:
            if os.path.exists(output_dir):
                for file_name in os.listdir(output_dir):
                    if file_name.endswith('.html'):
                        file_path = os.path.join(output_dir, file_name)
                        if file_path not in processed_files:
                            format_html_file(file_path)
        
    log_message(f"⏱️ Monitoraggio avviato. Controllo ogni {CHECK_INTERVAL} secondi")
    
    try:
        # Loop principale
        while True:
            if check_for_new_files():
                log_message("✅ File processati")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        log_message("🛑 Post-processore interrotto dall'utente")
    except Exception as e:
        import traceback
        log_message(f"❌ Errore nel loop principale: {str(e)}")
        log_message(traceback.format_exc())
    
    log_message("👋 Post-processore terminato")

if __name__ == "__main__":
    main()