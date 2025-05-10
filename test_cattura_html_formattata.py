import requests
URL = "http://127.0.0.1:7860"

try:
    r = requests.get(URL, timeout=5)
    r.raise_for_status()
    html = r.text
except Exception as e:
    print(f"[✖] Errore di connessione a {URL}: {e}")
    exit(1)

if "<table" in html.lower():
    print("[✔] Trovato almeno un tag <table> nella risposta HTML.")
else:
    print("[✖] Nessun tag <table> trovato nella risposta HTML.")
