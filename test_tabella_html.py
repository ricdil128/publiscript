import os
import time
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# HTML di esempio con una tabella
HTML_TEST = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Tabella HTML</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>Test Tabella per PubliScript</h1>
    
    <div class="chat-wrapper">
        <div class="desc">
            <div>
                <div>
                    <div>
                        <h2>Analisi Gap per Python for Beginners</h2>
                        <p>Ecco una tabella di esempio per testare il salvataggio:</p>
                        
                        <table>
                            <thead>
                                <tr>
                                    <th>Problema segnalato</th>
                                    <th>Frequenza</th>
                                    <th>Opportunità editoriale</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Mancanza di esempi pratici</td>
                                    <td>Alta</td>
                                    <td>Aggiungere più esempi realistici di codice</td>
                                </tr>
                                <tr>
                                    <td>Esercizi troppo complessi</td>
                                    <td>Media</td>
                                    <td>Graduale incremento di difficoltà con soluzioni guidate</td>
                                </tr>
                                <tr>
                                    <td>Spiegazioni poco chiare su OOP</td>
                                    <td>Alta</td>
                                    <td>Sezione dedicata con analogie reali e diagrammi</td>
                                </tr>
                                <tr>
                                    <td>Capitoli sulla gestione errori insufficienti</td>
                                    <td>Media</td>
                                    <td>Ampliare la sezione con casi d'uso comuni e pratiche</td>
                                </tr>
                                <tr>
                                    <td>Esempi di progetti troppo ridotti</td>
                                    <td>Alta</td>
                                    <td>Includere 2-3 progetti completi con step-by-step</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <p>Conclusione: migliorare gli esempi pratici e le spiegazioni complesse.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

class MockBookBuilder:
    """Classe mock per simulare AIBookBuilder"""
    
    def __init__(self):
        self.driver = None
        self.log_messages = []
    
    def add_log(self, message):
        print(message)
        self.log_messages.append(message)
    
    def get_current_keyword(self):
        return "Test_Tabella"
    
    def setup_browser(self):
        """Configura un browser per il test"""
        options = Options()
        options.add_argument("--headless")  # Nascondi il browser
        self.driver = webdriver.Chrome(options=options)
        
        # Crea un file HTML temporaneo
        with open("temp_test_table.html", "w", encoding="utf-8") as f:
            f.write(HTML_TEST)
        
        # Carica il file nel browser
        self.driver.get("file:///" + os.path.abspath("temp_test_table.html"))
        time.sleep(1)  # Breve attesa per il caricamento
    
    def test_save_methods(self):
        """Testa entrambi i metodi di salvataggio"""
        from ui.book_builder import AIBookBuilder
        
        if not self.driver:
            self.setup_browser()
        
        # Crea un'istanza di AIBookBuilder e assegna il driver
        book_builder = AIBookBuilder()
        book_builder.driver = self.driver
        book_builder.add_log = self.add_log
        book_builder.get_current_keyword = self.get_current_keyword
        
        # Test del primo metodo
        print("\n=== TEST DEL PRIMO METODO (save_complete_html) ===")
        html_file1 = book_builder.save_complete_html()
        
        # Test del secondo metodo
        print("\n=== TEST DEL SECONDO METODO (save_complete_html_improved) ===")
        html_file2 = book_builder.save_complete_html_improved()
        
        print("\n=== RISULTATI ===")
        print(f"File salvati:\n1. {html_file1}\n2. {html_file2}")
        print("\nCONFRONTA I FILE NEL BROWSER PER VEDERE LE DIFFERENZE")
        
        # Apri entrambi i file nel browser
        webbrowser.open("file:///" + os.path.abspath(html_file1))
        time.sleep(1)
        webbrowser.open("file:///" + os.path.abspath(html_file2))
        
        # Pulizia
        input("Premi Enter per terminare il test e chiudere il browser...")
        self.driver.quit()
        try:
            os.remove("temp_test_table.html")
        except:
            pass

if __name__ == "__main__":
    test = MockBookBuilder()
    test.test_save_methods()