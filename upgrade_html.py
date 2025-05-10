def upgrade_existing_html_files():
    """
    Migliora tutti i file HTML esistenti nella cartella output/genspark_formatted
    aggiungendo CSS appropriato e migliorando la formattazione delle tabelle.
    """
    import os
    import re
    
    # Ottieni tutti i file HTML nella directory specifica
    output_dir = os.path.join("output", "genspark_formatted")
    if not os.path.exists(output_dir):
        print(f"Directory {output_dir} non trovata")
        return
        
    html_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
    if not html_files:
        print("Nessun file HTML trovato nella directory output/genspark_formatted")
        return
    
    print(f"Trovati {len(html_files)} file HTML da migliorare")
    
    # CSS avanzato per le tabelle
    css_styles = """
    body { 
        font-family: Arial, sans-serif; 
        line-height: 1.6; 
        max-width: 1000px; 
        margin: 0 auto; 
        padding: 20px;
        background-color: #f9f9f9;
    }
    .header {
        background-color: #2563eb;
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1, h2, h3, h4 { 
        color: #2563eb; 
        margin-top: 24px; 
        margin-bottom: 16px; 
    }
    .metadata {
        background-color: #f0f4f8;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #2563eb;
    }
    table { 
        border-collapse: collapse; 
        width: 100%; 
        margin: 20px 0;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    th, td { 
        border: 1px solid #ddd; 
        padding: 12px; 
        text-align: left; 
    }
    th { 
        background-color: #f2f2f2; 
        font-weight: bold;
    }
    tr:nth-child(even) { 
        background-color: #f9f9f9; 
    }
    .content {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    ul, ol {
        margin-top: 15px;
        margin-bottom: 15px;
    }
    li {
        margin-bottom: 8px;
    }
    .ai-response {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 25px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #2563eb;
    }
    """
    
    # Processa ogni file
    for html_file in html_files:
        file_path = os.path.join(output_dir, html_file)
        
        try:
            # Leggi il file HTML
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Prova prima con BeautifulSoup
            try:
                from bs4 import BeautifulSoup
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Aggiungi CSS al tag <head>
                if soup.head:
                    # Rimuovi eventuali stili esistenti
                    for style in soup.head.find_all('style'):
                        style.decompose()
                    
                    style_tag = soup.new_tag('style')
                    style_tag.string = css_styles
                    soup.head.append(style_tag)
                else:
                    head_tag = soup.new_tag('head')
                    style_tag = soup.new_tag('style')
                    style_tag.string = css_styles
                    head_tag.append(style_tag)
                    if soup.html:
                        soup.html.insert(0, head_tag)
                
                # Migliora tabelle
                for table in soup.find_all('table'):
                    # Aggiungi classe alla tabella
                    if 'class' in table.attrs:
                        if 'data-table' not in table['class']:
                            table['class'].append('data-table')
                    else:
                        table['class'] = 'data-table'
                    
                    # Assicurati che ci siano thead e tbody
                    if not table.find('thead') and table.find('tr'):
                        first_row = table.find('tr')
                        thead = soup.new_tag('thead')
                        first_row.wrap(thead)
                        
                        # Converti td in th nell'header
                        for td in first_row.find_all('td'):
                            th = soup.new_tag('th')
                            th.string = td.get_text()
                            td.replace_with(th)
                
                # Salva il file sovrascrivendo l'originale
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                print(f"File migliorato: {file_path}")
                
            except ImportError:
                print("BeautifulSoup non installato, usando regex basic")
                
                # Aggiunta CSS con regex
                head_pattern = r'<head>(.*?)</head>'
                if re.search(head_pattern, content, re.DOTALL):
                    # Rimuovi eventuali tag style esistenti
                    content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
                    content = re.sub(head_pattern, f'<head>\\1<style>{css_styles}</style></head>', content, flags=re.DOTALL)
                else:
                    content = content.replace('<html>', f'<html><head><style>{css_styles}</style></head>')
                
                # Migliora le tabelle con regex
                table_pattern = r'<table[^>]*>(.*?)</table>'
                
                def enhance_table(match):
                    table_content = match.group(1)
                    # Se la tabella non ha thead, aggiungi
                    if '<thead>' not in table_content and '<tr>' in table_content:
                        first_row_match = re.search(r'<tr>(.*?)</tr>', table_content, re.DOTALL)
                        if first_row_match:
                            first_row = first_row_match.group(0)
                            # Converti td in th
                            enhanced_row = first_row.replace('<td>', '<th>').replace('</td>', '</th>')
                            # Avvolgi in thead
                            enhanced_thead = f'<thead>{enhanced_row}</thead>'
                            table_content = table_content.replace(first_row, enhanced_thead, 1)
                    
                    return f'<table class="data-table">{table_content}</table>'
                
                content = re.sub(table_pattern, enhance_table, content, flags=re.DOTALL)
                
                # Salva il file sovrascrivendo l'originale
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"File migliorato con regex: {file_path}")
                
        except Exception as e:
            print(f"Errore nel processare {html_file}: {str(e)}")
    
    print("Operazione completata!")

# Esegui lo script
if __name__ == "__main__":
    upgrade_existing_html_files()