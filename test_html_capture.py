"""
Test diretto della cattura e formattazione HTML senza integrarlo nell'interfaccia.
Questo script può essere eseguito separatamente per verificare che la funzionalità funzioni.
"""
import os
import sys
import re
from datetime import datetime
import traceback

# Converti tabelle markdown in HTML
def format_markdown_table(table_text):
    """Converte una tabella markdown in HTML"""
    if not table_text or '|' not in table_text:
        return table_text
    
    rows = table_text.strip().split('\n')
    if len(rows) < 2:
        return table_text
    
    html_table = '<table class="data-table">\n'
    
    # Intestazione
    header_cells = [cell.strip() for cell in rows[0].strip('|').split('|')]
    html_table += '  <thead>\n    <tr>\n'
    for cell in header_cells:
        if cell.strip():
            html_table += f'      <th>{cell}</th>\n'
    html_table += '    </tr>\n  </thead>\n'
    
    # Corpo della tabella
    html_table += '  <tbody>\n'
    for row in rows[2:]:  # Salta intestazione e separatore
        if '---' in row:  # Salta righe di separazione
            continue
            
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        html_table += '    <tr>\n'
        for cell in cells:
            if cell.strip():
                html_table += f'      <td>{cell}</td>\n'
        html_table += '    </tr>\n'
    
    html_table += '  </tbody>\n</table>'
    return html_table

# Prova a leggere un file HTML esistente nella directory output/genspark_formatted
def test_with_existing_html():
    print("\n=== TEST CON FILE HTML ESISTENTI ===")
    
    # Cerca file HTML nella directory
    output_dir = os.path.join("output", "genspark_formatted")
    if not os.path.exists(output_dir):
        print(f"❌ Directory {output_dir} non trovata")
        return
        
    html_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
    if not html_files:
        print(f"❌ Nessun file HTML trovato in {output_dir}")
        return
        
    # Seleziona il file più recente
    html_file = max(html_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
    html_path = os.path.join(output_dir, html_file)
    
    print(f"📝 Elaborazione del file: {html_file}")
    
    try:
        # Leggi il contenuto del file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        print(f"📄 File letto: {len(html_content)} caratteri")
        
        # Estrai solo il corpo del contenuto
        body_pattern = r'<body.*?>(.*?)</body>'
        body_match = re.search(body_pattern, html_content, re.DOTALL)
        
        if body_match:
            body_content = body_match.group(1)
            print(f"✅ Contenuto del body estratto: {len(body_content)} caratteri")
        else:
            print("⚠️ Tag body non trovati, utilizzo il contenuto completo")
            body_content = html_content
        
        # Crea un file HTML formattato correttamente
        keyword = html_file.split('_')[0].replace('_', ' ')
        
        # Cerca tabelle in formato markdown
        table_pattern = r'(\|[^\n]+\|\n\|[\-\|: ]+\|\n(?:\|[^\n]+\|\n)+)'
        formatted_content = re.sub(table_pattern, lambda m: format_markdown_table(m.group(1)), body_content)
        
        final_html = f"""<!DOCTYPE html>
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
        p {{
            margin-bottom: 15px;
            line-height: 1.7;
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
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Analisi: {keyword}</h1>
            <p>File originale: {html_file}</p>
        </header>
        
        <div class="content">
            {formatted_content}
        </div>
        
        <footer style="text-align: center; padding: 20px; color: #666;">
            <p>Test di formattazione - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </footer>
    </div>
</body>
</html>"""
        
        # Salva il nuovo file
        test_output_dir = os.path.join("output", "test_formatted")
        os.makedirs(test_output_dir, exist_ok=True)
        
        output_file = os.path.join(test_output_dir, f"reformatted_{html_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        print(f"✅ HTML formattato salvato in: {output_file}")
        
        # Apri il file nel browser
        import webbrowser
        try:
            webbrowser.open(f"file:///{os.path.abspath(output_file)}")
            print("✅ File HTML aperto nel browser")
        except Exception as e:
            print(f"⚠️ Impossibile aprire il browser: {str(e)}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Errore nel test: {str(e)}")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    print("🧪 Avvio test di cattura e formattazione HTML")
    output_file = test_with_existing_html()
    print("🧪 Test completato")