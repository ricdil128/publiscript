import os
import time
import webbrowser
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_genspark_table_formatting():
    """
    Test per verificare la formattazione di una tabella reale di Genspark.
    """
    print("Avvio test con tabella reale di Genspark...")
    
    # URL della conversazione Genspark
    genspark_url = "https://www.genspark.ai/agents?id=4ab0b330-5bdc-4b7f-be14-316f38c9f842"
    
    # Crea un'istanza del browser
    options = Options()
    driver = webdriver.Chrome(options=options)
    print(f"Browser Chrome avviato, apertura URL: {genspark_url}")
    
    try:
        # Apri l'URL di Genspark
        driver.get(genspark_url)
        print("Pagina Genspark caricata, attesa di 10 secondi per il rendering completo...")
        time.sleep(10)  # Attesa più lunga per caricare completamente la pagina Genspark
        
        # Cattura screenshot dell'intera pagina per riferimento
        screenshot_full = "genspark_full_page.png"
        driver.save_screenshot(screenshot_full)
        print(f"Screenshot della pagina completa salvato: {screenshot_full}")
        
        # Cerca l'elemento contenente la tabella
        print("Ricerca elemento contenente la risposta con tabella...")
        elements = driver.find_elements(By.CSS_SELECTOR, "div.chat-wrapper div.desc > div > div > div")
        
        if not elements:
            print("⚠️ Nessun elemento risposta trovato, provo un selettore più generico...")
            elements = driver.find_elements(By.CSS_SELECTOR, "div.chat-wrapper")
        
        if not elements:
            raise Exception("Nessun elemento risposta trovato nella pagina")
        
        chat_element = elements[0]
        print(f"Elemento trovato, dimensioni: {chat_element.size}")
        
        # Cattura screenshot dell'elemento risposta
        screenshot_element = "genspark_response_element.png"
        chat_element.screenshot(screenshot_element)
        print(f"Screenshot dell'elemento risposta salvato: {screenshot_element}")
        
        # Verifica presenza di tabelle tramite JavaScript
        table_count = driver.execute_script("""
            const responseElement = document.querySelector('div.chat-wrapper div.desc > div > div > div');
            if (!responseElement) return 0;
            return responseElement.querySelectorAll('table').length;
        """)
        
        print(f"Tabelle trovate nell'elemento: {table_count}")
        
        if table_count == 0:
            # Stampa HTML per debug
            html_content = driver.execute_script("""
                const responseElement = document.querySelector('div.chat-wrapper div.desc > div > div > div');
                return responseElement ? responseElement.innerHTML : 'Elemento non trovato';
            """)
            
            print("HTML dell'elemento risposta:")
            print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
            
            # Cerca tabelle con formato Markdown
            markdown_tables = driver.execute_script("""
                const responseElement = document.querySelector('div.chat-wrapper div.desc > div > div > div');
                if (!responseElement) return 0;
                const text = responseElement.textContent;
                
                // Cerca tabelle in formato Markdown
                const tablePattern = /\\|[^\\n]+\\|[\\n\\s]*\\|[\\s\\-:]+\\|/g;
                const matches = text.match(tablePattern);
                return matches ? matches.length : 0;
            """)
            
            print(f"Potenziali tabelle Markdown trovate: {markdown_tables}")
            
            if markdown_tables > 0:
                print("⚠️ La tabella sembra essere in formato Markdown, non HTML!")
        
        # Script JavaScript per formattare le tabelle (versione avanzata)
        js_code = """
        function analyzeAndProcess(element) {
            if (!element) return {html: '', info: 'Elemento non trovato'};
            
            // Clone l'elemento per non modificare il DOM originale
            const clone = element.cloneNode(true);
            const info = {};
            
            // Analizza il contenuto
            info.textLength = element.textContent.length;
            info.innerHTML = element.innerHTML.length;
            
            // Cerca tabelle HTML
            const tables = clone.querySelectorAll('table');
            info.tablesCount = tables.length;
            
            if (tables.length > 0) {
                info.tableStructure = [];
                
                // Processa ogni tabella
                for (let t = 0; t < tables.length; t++) {
                    const table = tables[t];
                    const tableInfo = {
                        rows: table.rows.length,
                        hasHeader: !!table.querySelector('th') || !!table.querySelector('thead'),
                        hasStyles: !!table.getAttribute('style')
                    };
                    
                    info.tableStructure.push(tableInfo);
                    
                    // Applica stili alla tabella
                    table.setAttribute('style', `
                        display: table !important;
                        width: 100% !important;
                        border-collapse: collapse !important;
                        margin: 15px 0 !important;
                        border: 1px solid #ddd !important;
                    `);
                    
                    // Gestisci thead e tbody
                    let thead = table.querySelector('thead');
                    let tbody = table.querySelector('tbody');
                    
                    // Se non c'è thead ma ci sono righe, usa la prima riga come header
                    if (!thead && table.rows.length > 0) {
                        const firstRow = table.rows[0];
                        const hasTh = firstRow.querySelector('th');
                        
                        // Se la prima riga contiene th o non c'è tbody, trattiamola come header
                        if (hasTh || !tbody) {
                            thead = document.createElement('thead');
                            thead.appendChild(firstRow.cloneNode(true));
                            if (firstRow.parentNode === table) {
                                table.insertBefore(thead, firstRow);
                                table.removeChild(firstRow);
                            }
                        }
                    }
                    
                    // Processa le righe in thead
                    if (thead) {
                        const headerRows = thead.querySelectorAll('tr');
                        for (let r = 0; r < headerRows.length; r++) {
                            headerRows[r].setAttribute('style', `
                                display: table-row !important;
                                background-color: #f2f2f2 !important;
                            `);
                            
                            // Processa le celle di intestazione
                            const cells = headerRows[r].querySelectorAll('th, td');
                            for (let c = 0; c < cells.length; c++) {
                                cells[c].setAttribute('style', `
                                    display: table-cell !important;
                                    border: 1px solid #ddd !important;
                                    padding: 8px !important;
                                    text-align: left !important;
                                    background-color: #f2f2f2 !important;
                                    font-weight: bold !important;
                                `);
                            }
                        }
                    }
                    
                    // Processa le righe in tbody o direttamente nella tabella
                    const rows = tbody ? tbody.querySelectorAll('tr') : table.querySelectorAll('tr');
                    let startIdx = 0;
                    
                    // Se non c'è thead ma abbiamo riconosciuto la prima riga come header
                    if (!thead && table.rows.length > 0) {
                        startIdx = 1;
                    }
                    
                    for (let r = startIdx; r < rows.length; r++) {
                        const row = rows[r];
                        const isEven = (r - startIdx) % 2 === 0;
                        
                        row.setAttribute('style', `
                            display: table-row !important;
                            background-color: ${isEven ? '#ffffff' : '#f9f9f9'} !important;
                        `);
                        
                        // Processa le celle
                        const cells = row.querySelectorAll('td, th');
                        for (let c = 0; c < cells.length; c++) {
                            const isHeaderCell = cells[c].tagName.toLowerCase() === 'th';
                            cells[c].setAttribute('style', `
                                display: table-cell !important;
                                border: 1px solid #ddd !important;
                                padding: 8px !important;
                                text-align: left !important;
                                vertical-align: top !important;
                                background-color: ${isHeaderCell ? '#f2f2f2' : 'inherit'} !important;
                                font-weight: ${isHeaderCell ? 'bold' : 'normal'} !important;
                            `);
                        }
                    }
                }
            } else {
                // Cerca tabelle in formato Markdown
                const text = element.textContent || '';
                const tablePattern = /\\|[^\\n]+\\|[\\n\\s]*\\|[\\s\\-:]+\\|/g;
                const matches = text.match(tablePattern);
                info.markdownTables = matches ? matches.length : 0;
                
                if (info.markdownTables > 0) {
                    info.markdownTablesSample = matches[0].substring(0, 100);
                    
                    // Qui si potrebbe aggiungere codice per convertire tabelle Markdown in HTML
                    // Ma per ora lo lasciamo come informazione diagnostica
                }
            }
            
            return {
                html: clone.outerHTML,
                info: info
            };
        }
        
        // Trova l'elemento risposta e processalo
        const responseElement = document.querySelector('div.chat-wrapper div.desc > div > div > div');
        return analyzeAndProcess(responseElement);
        """
        
        # Esegui lo script JavaScript avanzato
        print("Esecuzione script JavaScript per analizzare e formattare tabelle...")
        result = driver.execute_script(js_code)
        
        # Estrai le informazioni di debug
        if isinstance(result, dict):
            html_output = result.get('html', '')
            info = result.get('info', {})
            print("\n--- Informazioni analisi tabella ---")
            print(f"Dimensioni testo: {info.get('textLength', 'N/A')} caratteri")
            print(f"Dimensioni HTML: {info.get('innerHTML', 'N/A')} caratteri")
            print(f"Tabelle HTML trovate: {info.get('tablesCount', 0)}")
            
            if info.get('markdownTables', 0) > 0:
                print(f"Tabelle Markdown trovate: {info.get('markdownTables', 0)}")
                print(f"Esempio tabella Markdown: {info.get('markdownTablesSample', 'N/A')}")
            
            if info.get('tableStructure'):
                for i, table_info in enumerate(info.get('tableStructure', [])):
                    print(f"\nTabella #{i+1}:")
                    print(f"  Righe: {table_info.get('rows', 'N/A')}")
                    print(f"  Ha intestazione: {table_info.get('hasHeader', False)}")
                    print(f"  Ha stili: {table_info.get('hasStyles', False)}")
        else:
            html_output = result
            print("⚠️ Informazioni di debug non disponibili")
        
        # Crea un file HTML completo con il risultato
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Tabella Genspark - {timestamp}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2 {{
            color: #2563eb;
        }}
        .content {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <h1>Test Formattazione Tabella Genspark</h1>
    <p>Generato il: {timestamp}</p>
    
    <div class="content">
        {html_output}
    </div>
</body>
</html>"""
        
        # Salva il file HTML
        output_file = f"genspark_table_test_{timestamp}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\nFile HTML risultato salvato: {output_file}")
        
        # Apri il file nel browser
        webbrowser.open("file:///" + os.path.abspath(output_file))
        print("File HTML aperto nel browser")
        
    except Exception as e:
        import traceback
        print(f"ERRORE: {str(e)}")
        print(traceback.format_exc())
    finally:
        # Chiedi all'utente se vuole chiudere il browser
        input("Premi Enter per chiudere il browser...")
        driver.quit()
        print("Browser chiuso")
        
    print("Test completato!")

if __name__ == "__main__":
    test_genspark_table_formatting()