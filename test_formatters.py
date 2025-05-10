"""
Script di test per verificare la formattazione delle tabelle HTML.
Esegui questo script separatamente per testare le funzionalità di formattazione.
"""

import os
import sys
import re
from datetime import datetime

# Aggiungi la directory principale al path per importare i moduli del progetto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Prova ad importare le funzioni di formattazione
try:
    # Prova prima con framework.formatters
    try:
        from framework.formatters import (
            process_text,
            process_table_html,
            format_analysis_results_html,
            save_analysis_to_html
        )
        print("✅ Moduli importati da framework.formatters")
    except ImportError:
        # Prova poi con percorso diretto
        module_dir = os.path.join(os.getcwd(), "framework")
        sys.path.append(module_dir)
        
        try:
            from formatters import (
                process_text,
                process_table_html,
                format_analysis_results_html,
                save_analysis_to_html
            )
            print("✅ Moduli importati da formatters.py nella directory", module_dir)
        except ImportError:
            # Ultimo tentativo - cerca in tutte le directory
            found = False
            for root, dirs, files in os.walk(os.getcwd()):
                if "formatters.py" in files:
                    print(f"📍 Trovato formatters.py in: {root}")
                    sys.path.append(root)
                    try:
                        from formatters import (
                            process_text, 
                            process_table_html,
                            format_analysis_results_html,
                            save_analysis_to_html
                        )
                        print("✅ Moduli importati da", root)
                        found = True
                        break
                    except ImportError:
                        print("❌ Impossibile importare da", root)
            
            if not found:
                print("❌ Non è stato possibile trovare i moduli di formattazione")
                
                # Definiamo funzioni minime per i test
                def process_text(text):
                    return text
                
                def process_table_html(content):
                    return f"<div>TABELLA NON FORMATTATA: {content}</div>"
                
                def format_analysis_results_html(keyword, market, book_type, language, context=None, log_callback=None, save_to_file=True, analysis_type=None):
                    return f"<h1>Analisi di test per {keyword}</h1>"
                
                def save_analysis_to_html(formatted_html, keyword, market, book_type, language, analysis_type="Legacy", log_callback=None):
                    return "test_output.html"
                
                print("⚠️ Utilizzando funzioni di fallback per i test")

except Exception as e:
    print(f"❌ Errore nell'importazione: {str(e)}")
    import traceback
    print(traceback.format_exc())
    
    # Definiamo funzioni minime
    def process_text(text):
        return text
    
    def process_table_html(content):
        return f"<div>TABELLA NON FORMATTATA: {content}</div>"
    
    def format_analysis_results_html(keyword, market, book_type, language, context=None, log_callback=None, save_to_file=True, analysis_type=None):
        return f"<h1>Analisi di test per {keyword}</h1>"
    
    def save_analysis_to_html(formatted_html, keyword, market, book_type, language, analysis_type="Legacy", log_callback=None):
        return "test_output.html"
    
    print("⚠️ Utilizzando funzioni di fallback per i test")


def log_message(message):
    """Funzione di logging per i test"""
    print(f"LOG: {message}")


def test_table_formatting():
    """Test della formattazione delle tabelle"""
    print("\n=== TEST FORMATTAZIONE TABELLE ===")
    
    # Esempio di tabella in formato markdown
    markdown_table = """
| Criterio | Digital Asset Trust Mastery | Crypto Estate Planning | The Digital Legacy Trust Blueprint |
|---------|------------------------|---------------------|----------------------------|
| Chiarezza | ★★★★☆ | ★★★★★ | ★★★★★ |
| Potere evocativo | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| Potenziale di vendita | ★★★★☆ | ★★★★★ | ★★★★☆ |
| Pertinenza tematica | ★★★★★ | ★★★★☆ | ★★★★★ |
| Compatibilità con buyer persona | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| TOTALE | 19/25 | 22/25 | 24/25 |
"""
    
    # Test 1: Formattazione tabella diretta
    print("\nTest 1: Formattazione tabella diretta")
    try:
        if 'process_table_html' in globals() and callable(process_table_html):
            formatted_table = process_table_html(markdown_table)
            print("Risultato formattazione tabella:")
            print("---")
            print(formatted_table[:200] + "..." if len(formatted_table) > 200 else formatted_table)
            print("---")
            
            # Verifica se la tabella è stata formattata correttamente
            if "<table" in formatted_table and "<tr" in formatted_table and "<td" in formatted_table:
                print("✅ Tabella formattata correttamente con tag HTML")
            else:
                print("❌ La tabella non contiene i tag HTML corretti")
        else:
            print("❌ Funzione process_table_html non disponibile")
    except Exception as e:
        print(f"❌ Errore nella formattazione tabella: {str(e)}")
    
    # Test 2: Process text con tabella
    print("\nTest 2: Process text con tabella")
    try:
        if 'process_text' in globals() and callable(process_text):
            text_with_table = f"Ecco una tabella di esempio:\n\n{markdown_table}\n\nFine della tabella."
            processed_text = process_text(text_with_table)
            print("Risultato process_text:")
            print("---")
            print(processed_text[:200] + "..." if len(processed_text) > 200 else processed_text)
            print("---")
            
            # Controlla se la tabella è rimasta o è stata processata
            if "<table" in processed_text or "<tr" in processed_text:
                print("✅ La tabella è stata convertita in HTML")
            else:
                print("⚠️ La tabella non è stata convertita in HTML durante process_text")
        else:
            print("❌ Funzione process_text non disponibile")
    except Exception as e:
        print(f"❌ Errore nel process_text: {str(e)}")
    
    # Test 3: Analisi completa
    print("\nTest 3: Generazione analisi completa con tabella")
    try:
        content_with_table = f"""
# Valutazione dei Titoli

Ecco una tabella che mostra la valutazione dei diversi titoli proposti:

{markdown_table}

## Scelta del Titolo Migliore

Il titolo "The Digital Legacy Trust Blueprint: A Step-by-Step System for Securing Your Cryptocurrency, Social Media, and Online Assets in Your Living Trust" emerge come la scelta ottimale con un punteggio di 24/25.
        """
        
        # Crea un contesto fittizio per il test
        test_context = {
            "KEYWORD": "Living Trust",
            "MARKET_INSIGHTS": "Il mercato dei trust digitali è in crescita del 15% annuo",
            "BUYER_PERSONA_SUMMARY": "Professionisti 40-60 anni con patrimonio digitale significativo",
            "ANGOLO_ATTACCO": "Sicurezza e protezione del patrimonio digitale",
            "TITOLO_LIBRO": "The Digital Legacy Trust Blueprint"
        }
        
        # Generazione HTML
        if 'format_analysis_results_html' in globals() and callable(format_analysis_results_html):
            html_result = format_analysis_results_html(
                keyword="Living Trust",
                market="USA",
                book_type="How-To Guide",
                language="English",
                context=test_context,
                log_callback=log_message,
                save_to_file=False,
                analysis_type="Test"
            )
            
            print("Risultato format_analysis_results_html:")
            print("---")
            print(html_result[:200] + "..." if len(html_result) > 200 else html_result)
            print("---")
            
            # Verifica se l'HTML contiene elementi di formattazione
            if "<table" in html_result or "<section" in html_result:
                print("✅ HTML generato con formattazione")
            else:
                print("⚠️ HTML generato senza formattazione avanzata")
                
            # Test finale: salva l'HTML in un file di test
            if 'save_analysis_to_html' in globals() and callable(save_analysis_to_html):
                output_path = save_analysis_to_html(
                    formatted_html=html_result,
                    keyword="Living Trust",
                    market="USA",
                    book_type="How-To Guide",
                    language="English",
                    analysis_type="Test",
                    log_callback=log_message
                )
                
                print(f"✅ File HTML salvato in: {output_path}")
                print("Verifica questo file per controllare la formattazione delle tabelle")
            else:
                print("❌ Funzione save_analysis_to_html non disponibile")
        else:
            print("❌ Funzione format_analysis_results_html non disponibile")
    except Exception as e:
        print(f"❌ Errore nella generazione analisi: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    print("🧪 Avvio test di formattazione delle tabelle")
    test_table_formatting()
    print("\n🧪 Test completati")