from selenium import webdriver
import time
import os
import webbrowser

def save_complete_html(driver, output_path="test_fullpage_capture.html"):
    """
    Salva l'intero DOM della pagina visibile nel browser con CSS.
    """
    try:
        # Attendi caricamento completo del DOM
        time.sleep(3)
        full_html = driver.execute_script("return document.documentElement.outerHTML")

        # Aggiungi <!DOCTYPE html> se manca
        if not full_html.lower().startswith("<!doctype"):
            full_html = f"<!DOCTYPE html>\n{full_html}"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        webbrowser.open(f"file:///{os.path.abspath(output_path)}")
        print(f"✅ HTML salvato in: {output_path}")
    except Exception as e:
        print(f"❌ Errore: {str(e)}")


# === TEST ===
if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.w3schools.com/html/html_tables.asp")  # pagina con tabelle e CSS

    save_complete_html(driver)

    driver.quit()
