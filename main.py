"""
Entry point principale per PubliScript.
Avvia l'interfaccia grafica o la modalità CLI in base ai parametri.
"""
import signal
import sys
import os
import argparse

# Import dei moduli principali
from ui.app_launcher import launch_app
from ui.book_builder import AIBookBuilder

def signal_handler(sig, frame):
    print('\nInterruzione rilevata, salvataggio cookies e chiusura browser...')
    
    # Accedi all'istanza globale del browser se esiste
    from ai_interfaces.browser_manager import _browser_instance
    
    if _browser_instance is not None:
        # Salva i cookies se la funzione è disponibile
        if hasattr(_browser_instance, 'save_cookies'):
            try:
                _browser_instance.save_cookies()
                print("✅ Cookies salvati con successo")
            except Exception as e:
                print(f"⚠️ Errore nel salvare i cookies: {e}")
        
        # Chiudi il browser
        try:
            _browser_instance.quit()
            print("✅ Browser chiuso correttamente")
        except Exception as e:
            print(f"⚠️ Errore nella chiusura del browser: {e}")
    
    print("👋 Applicazione terminata. Arrivederci!")
    sys.exit(0)

# Registra i gestori di segnali
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Terminazione (kill)

# Stampa messaggio informativo
print("ℹ️ Premere Ctrl+C per terminare l'applicazione e salvare i cookies")

def main():
    """Funzione principale per avviare l'applicazione."""
    parser = argparse.ArgumentParser(description="PubliScript - Sistema per analisi e generazione di libri")
    parser.add_argument("--cli", action="store_true", help="Avvia in modalità CLI invece che GUI")
    parser.add_argument("--book-title", type=str, help="Titolo del libro (solo CLI)")
    
    args = parser.parse_args()
    
    if args.cli:
        # Modalità CLI (da implementare)
        print("Modalità CLI non ancora implementata")
    else:
        # Modalità GUI (default)
        launch_app()

if __name__ == "__main__":
    main()