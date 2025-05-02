# cleanup_simple_test.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os

def setup_browser():
    """Configura e avvia un'istanza di Chrome."""
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.add_argument("--start-maximized")
    
    # Senza installazione automatica del driver
    driver = webdriver.Chrome(options=options)
    return driver

def take_screenshot(driver, name):
    """Salva uno screenshot."""
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    
    filename = f"screenshots/{name}_{int(time.time())}.png"
    driver.save_screenshot(filename)
    print(f"Screenshot salvato: {filename}")
    return filename

def wait_for_user_action(message):
    """Attende input dall'utente."""
    input(f"\n{message} - Premi INVIO per continuare...")

def main():
    driver = None
    try:
        # 1. Avvio browser
        print("Avvio browser...")
        driver = setup_browser()
        
        # 2. Naviga a Genspark
        print("Navigazione a Genspark...")
        driver.get("https://www.genspark.ai/")
        
        # 3. Attendi login manuale
        wait_for_user_action("Accedi manualmente a Genspark e naviga alla chat")
        
        # 4. Cattura URL e screenshot
        print(f"URL corrente: {driver.current_url}")
        take_screenshot(driver, "after_login")
        
        # 5. Attendi fino a quando l'utente è pronto per inviare un messaggio che causi abort
        wait_for_user_action("Ora verrà inviato un messaggio che potrebbe causare un abort. Sei pronto?")
        
        # 6. Trova la casella di input
        input_selector = input("Incolla qui il selettore CSS della casella di input (o premi invio per quello predefinito): ") or "div.search-input-wrapper textarea"
        
        try:
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
            )
            
            # 7. Invia il messaggio problematico
            print("Invio messaggio problematico...")
            input_box.send_keys("3) Analizza i 3 migliori concorrenti per la keyword Companion Planting su Amazon.com nel mercato USA: mostra per ciascuno titolo, sottotitolo, BSR, recensioni, struttura (indice se disponibile), copertina (stile, elementi distintivi), pricing, e bonus offerti; concludi con una mini-tabella comparativa e insight su ciò che li rende forti; scrivi in Italiano, titoli e keyword nella lingua del USA; concludi con la parola FINE.")
            
            # 8. Clicca il pulsante di invio
            send_selector = input("Incolla qui il selettore CSS del pulsante di invio (o premi invio per quello predefinito): ") or "div.search-input-wrapper div.input-icon"
            send_button = driver.find_element(By.CSS_SELECTOR, send_selector)
            send_button.click()
            
            # 9. Attendi che si verifichi l'abort
            wait_for_user_action("Quando vedi la risposta abortita, premi INVIO")
            take_screenshot(driver, "aborted_response")
            
            # 10. Menu di operazioni
            while True:
                print("\nTest di pulizia chat - Menu operazioni:")
                print("1. Ricarica pagina")
                print("2. Naviga a URL specifico")
                print("3. Testa selettore CSS specifico")
                print("4. Testa selettore XPATH specifico")
                print("5. Invia sequenza di tasti")
                print("6. Esegui script JavaScript")
                print("7. Cattura screenshot")
                print("8. Esci")
                
                choice = input("\nSeleziona operazione (1-8): ")
                
                if choice == "1":
                    driver.refresh()
                    print("Pagina ricaricata")
                    print(f"URL corrente: {driver.current_url}")
                
                elif choice == "2":
                    url = input("Inserisci URL: ")
                    driver.get(url)
                    print(f"Navigato a: {driver.current_url}")
                
                elif choice == "3":
                    css = input("Inserisci selettore CSS: ")
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, css)
                        print(f"Trovati {len(elements)} elementi")
                        
                        if elements:
                            for i, el in enumerate(elements[:5]):
                                text = el.text.strip() if el.text else "[No text]"
                                print(f"Elemento {i}: '{text[:30]}...'")
                                
                            action = input("Clicca elemento numero (0-n) o 'skip' per saltare: ")
                            if action != "skip":
                                try:
                                    elements[int(action)].click()
                                    print("Click eseguito")
                                except Exception as e:
                                    print(f"Errore nel click: {str(e)}")
                    except Exception as e:
                        print(f"Errore: {str(e)}")
                
                elif choice == "4":
                    xpath = input("Inserisci selettore XPATH: ")
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        print(f"Trovati {len(elements)} elementi")
                        
                        if elements:
                            for i, el in enumerate(elements[:5]):
                                text = el.text.strip() if el.text else "[No text]"
                                print(f"Elemento {i}: '{text[:30]}...'")
                                
                            action = input("Clicca elemento numero (0-n) o 'skip' per saltare: ")
                            if action != "skip":
                                try:
                                    elements[int(action)].click()
                                    print("Click eseguito")
                                except Exception as e:
                                    print(f"Errore nel click: {str(e)}")
                    except Exception as e:
                        print(f"Errore: {str(e)}")
                
                elif choice == "5":
                    keys = input("Inserisci sequenza tasti (es: CTRL+R): ")
                    try:
                        webdriver.ActionChains(driver).send_keys(keys).perform()
                        print("Sequenza tasti inviata")
                    except Exception as e:
                        print(f"Errore: {str(e)}")
                
                elif choice == "6":
                    script = input("Inserisci script JavaScript: ")
                    try:
                        result = driver.execute_script(script)
                        print(f"Script eseguito, risultato: {result}")
                    except Exception as e:
                        print(f"Errore: {str(e)}")
                
                elif choice == "7":
                    name = input("Nome screenshot: ")
                    take_screenshot(driver, name)
                
                elif choice == "8":
                    print("Uscita...")
                    break
                
                # Dopo ogni azione, verifica se è possibile trovare l'input box
                try:
                    input_box = driver.find_element(By.CSS_SELECTOR, input_selector)
                    if input_box.is_displayed():
                        print("✅ Input box accessibile!")
                        take_screenshot(driver, "input_box_accessible")
                except:
                    print("❌ Input box non accessibile")
                
        except Exception as e:
            print(f"Errore: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
    except Exception as e:
        print(f"Errore generale: {str(e)}")
    finally:
        if driver:
            wait_for_user_action("Premi INVIO per chiudere il browser")
            driver.quit()

if __name__ == "__main__":
    main()