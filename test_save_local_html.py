from selenium import webdriver
import os
import time
import webbrowser

def save_complete_html(driver, output_file="saved_test_page.html"):
    time.sleep(1)  # attende il caricamento
    html = driver.execute_script("return document.documentElement.outerHTML")
    if not html.lower().startswith("<!doctype"):
        html = "<!DOCTYPE html>\n" + html

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    webbrowser.open("file://" + os.path.abspath(output_file))
    print(f"✅ HTML salvato: {output_file}")

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # per vedere visivamente, lascia disattivo

    driver = webdriver.Chrome(options=options)

    local_path = os.path.abspath("test_page.html")
    driver.get("file://" + local_path)

    save_complete_html(driver)
    driver.quit()
