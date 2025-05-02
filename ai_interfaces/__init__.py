"""
Interfacce per interazione con AI come Genspark.
"""

from .browser_manager import setup_browser, check_login, create_fresh_chat
from .interaction_utils import get_input_box
from .browser_manager import setup_browser, debug_setup_browser
# Rimuovi l'import di send_to_genspark che non esiste come funzione indipendente
from .interaction_utils import send_prompt_and_wait_for_response, clear_chat
from .file_text_utils import sanitize_filename, clean_text, split_text, load_config

# Se serve utilizzare send_to_genspark, importare il modulo che contiene la classe
# che lo implementa, ad esempio:
# from ui.book_builder import AIBookBuilder

# Opzionalmente, puoi creare un wrapper se desideri comunque fornire una funzione
# send_to_genspark a livello di modulo:
def send_to_genspark(driver, text, prompt_id=None, section_number=None):
    """
    Wrapper per l'accesso alla funzionalità di send_to_genspark implementata in AIBookBuilder
    """
    # Importa localmente per evitare import circolari
    from ui.book_builder import AIBookBuilder
    
    # Crea una istanza temporanea o usa istanze esistenti
    # Questo è solo un esempio, potresti voler gestire questo diversamente
    builder = AIBookBuilder.get_instance() if hasattr(AIBookBuilder, 'get_instance') else None
    
    if builder:
        return builder.send_to_genspark(text, prompt_id, section_number)
    else:
        # Fallback a una versione semplificata
        from .interaction_utils import send_prompt_and_wait_for_response, get_input_box
        print(f"⚠️ Utilizzo versione semplificata di send_to_genspark (senza AIBookBuilder)")
        
        input_box = get_input_box(driver)
        if not input_box:
            print("❌ Input box non trovato")
            return "ERRORE: Input box non disponibile"
        
        return send_prompt_and_wait_for_response(driver, input_box, text)