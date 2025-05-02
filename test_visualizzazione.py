# test_visualizzazione.py - Test della visualizzazione dei risultati
import os
import re

def test_parsing_contesto():
    """Testa la capacità di estrarre sezioni dal file di contesto"""
    print("🧪 Test parsing contenuto context.txt...")
    
    try:
        # Verifica esistenza file
        context_file = "context.txt"
        if not os.path.exists(context_file):
            print(f"❌ File {context_file} non trovato")
            return False
            
        # Leggi contenuto
        with open(context_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"Letto file context.txt: {len(content)} caratteri")
        
        # Testa il pattern di estrazione sezioni
        section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
        section_matches = re.findall(section_pattern, content, re.DOTALL)
        
        if section_matches:
            print(f"✅ Trovate {len(section_matches)} sezioni nel formato standard")
            for i, (title, _) in enumerate(section_matches[:3]):  # Mostra solo prime 3
                print(f"  - Sezione {i+1}: {title}")
            return True
        else:
            print("❌ Nessuna sezione trovata con il pattern standard")
            
            # Prova pattern alternativi
            alt_pattern = r'(\d+\).*?)(?=\d+\)|$)'
            alt_matches = re.findall(alt_pattern, content, re.DOTALL)
            
            if alt_matches:
                print(f"✅ Trovate {len(alt_matches)} sezioni con pattern numerico")
                for i, match in enumerate(alt_matches[:3]):
                    preview = match[:50].replace('\n', ' ')
                    print(f"  - Sezione {i+1}: {preview}...")
                return True
            else:
                print("❌ Nessuna sezione trovata con pattern alternativi")
                return False
    
    except Exception as e:
        print(f"❌ Errore durante il test: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

def create_test_html():
    """Crea un HTML di test basato sul contenuto del context.txt"""
    try:
        # Verifica esistenza file
        context_file = "context.txt"
        if not os.path.exists(context_file):
            print(f"❌ File {context_file} non trovato")
            return False
            
        # Leggi contenuto
        with open(context_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"Letto file context.txt: {len(content)} caratteri")
        
        # Estrai sezioni
        sections = []
        section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n(.*?)(?=\n===|$)'
        section_matches = re.findall(section_pattern, content, re.DOTALL)
        
        if section_matches:
            sections = [(title.strip(), content.strip()) for title, content in section_matches]
        else:
            # Fallback: divide il testo per numeri progressivi
            number_pattern = r'(\d+\).*?)(?=\d+\)|$)'
            number_matches = re.findall(number_pattern, content, re.DOTALL)
            
            if number_matches:
                sections = [(f"Sezione {i+1}", content.strip()) for i, content in enumerate(number_matches)]
            else:
                # Ultimo fallback: usa il testo completo
                sections = [("Risultati completi", content)]
        
        # Genera HTML
        html = """
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Visualizzazione PubliScript</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { background: linear-gradient(to right, #2563eb, #4f46e5); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .section { background-color: #f3f4f6; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
                .section-title { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
                .section-content { white-space: pre-wrap; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Test Visualizzazione Risultati</h1>
                <p>Questo è un test per verificare come vengono visualizzati i risultati dell'analisi.</p>
            </div>
        """
        
        for title, content in sections:
            html += f"""
            <div class="section">
                <div class="section-title">{title}</div>
                <div class="section-content">{content}</div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        # Salva file HTML
        output_file = "test_visualizzazione.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"✅ File HTML di test creato: {output_file}")
        print(f"Apri questo file in un browser per verificare la visualizzazione")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la creazione dell'HTML: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_parsing_contesto()
    create_test_html()