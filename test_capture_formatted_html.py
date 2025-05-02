# test_capture_formatted_html.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from datetime import datetime
import webbrowser

def capture_formatted_response(driver):
    """
    Cattura la risposta formattata direttamente dall'interfaccia di Genspark.
    """
    try:
        print("Cercando elementi di risposta...")
        
        # Prova diversi selettori per trovare le risposte
        selectors = [
            ".message-content", 
            "div.chat-message-item .content",
            "div.chat-wrapper div.desc > div > div",
            "div.message-list div.message div.text-wrap",
            "div.response-content"
        ]
        
        response_elements = None
        for selector in selectors:
            print(f"Provo il selettore: {selector}")
            response_elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if response_elements and len(response_elements) > 0:
                print(f"✅ Trovati {len(response_elements)} elementi con selettore {selector}")
                break
        
        if not response_elements or len(response_elements) == 0:
            print("❌ Nessun elemento di risposta trovato con nessun selettore")
            
            # Debug - Stampa l'HTML della pagina
            print("=== HTML della pagina per debug ===")
            page_source = driver.page_source[:500]  # Solo i primi 500 caratteri
            print(page_source + "...")
            
            return None
        
        print(f"Analizzando {len(response_elements)} risposte trovate")
            
        # Prendiamo l'ultimo elemento (la risposta più recente)
        response_element = response_elements[-1]
        
        # Debug info
        text_preview = response_element.text[:100] if response_element.text else "No text"
        print(f"Preview del testo dell'elemento: {text_preview}...")
        
        # Ottieni l'HTML interno dell'elemento con JavaScript
        formatted_html = driver.execute_script("""
            return arguments[0].innerHTML;
        """, response_element)
        
        # Alternativa se la prima non funziona
        if not formatted_html:
            formatted_html = driver.execute_script("""
                return arguments[0].outerHTML;
            """, response_element)
        
        if formatted_html:
            print(f"✅ HTML formattato acquisito: {len(formatted_html)} caratteri")
            print(f"Preview HTML: {formatted_html[:150]}...")
            
            # Aggiungi stili CSS necessari per una corretta visualizzazione
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                    code {{ background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    h1, h2, h3, h4 {{ color: #333; margin-top: 24px; margin-bottom: 16px; }}
                    img {{ max-width: 100%; height: auto; }}
                    .highlight {{ background-color: #ffeb3b; padding: 2px; }}
                    
                    /* Stili aggiuntivi per elementi Genspark */
                    .markdown-content p {{ margin: 0.5em 0; }}
                    .markdown-content ul, .markdown-content ol {{ padding-left: 20px; }}
                </style>
                <title>Analisi Genspark</title>
            </head>
            <body>
                <h1>Contenuto Formattato da Genspark</h1>
                <div class="genspark-response">
                    {formatted_html}
                </div>
            </body>
            </html>
            """
            
            return styled_html
        else:
            print("❌ HTML formattato vuoto")
            return None
            
    except Exception as e:
        print(f"❌ Errore nel catturare l'HTML formattato: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    print("Avvio test di cattura HTML formattato...")
    
    # Configurazione del browser
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    
    # Usa il Chrome normale invece di undetected_chromedriver
    driver = webdriver.Chrome(options=options)
    
    try:
        # Naviga a Genspark
        print("Navigando a Genspark...")
        driver.get("https://genspark.ai")
        
        # Attendi che l'utente faccia login manualmente
        print("\n" + "="*80)
        print("ATTENZIONE: Per favore, fai login manualmente e naviga")
        print("a una chat con una risposta formattata.")
        print("Una volta che la risposta è visibile, premi Enter per continuare.")
        print("="*80 + "\n")
        input("Premi Enter quando sei pronto per catturare la risposta...")
        
        # Cattura l'HTML formattato
        print("Cattura dell'HTML formattato in corso...")
        formatted_html = capture_formatted_response(driver)
        
        if formatted_html:
            # Salva l'HTML in un file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs("test_output", exist_ok=True)
            html_path = f"test_output/genspark_formatted_{timestamp}.html"
            
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(formatted_html)
            
            print(f"✅ HTML formattato salvato in: {html_path}")
            
            # Apri il file nel browser
            abs_path = os.path.abspath(html_path)
            print(f"Apertura automatica di: {abs_path}")
            webbrowser.open(f"file://{abs_path}")
        else:
            print("❌ Impossibile catturare l'HTML formattato")
    
    finally:
        # Chiedi all'utente se vuole chiudere il browser
        input("Premi Enter per chiudere il browser...")
        driver.quit()
        print("Browser chiuso")

if __name__ == "__main__":
    main()