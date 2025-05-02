"""
Modulo di utilità generali per il framework.
"""

import logging
import time
from typing import Any, Callable, Optional

def execute_with_updates(func: Callable, log_callback: Optional[Callable] = None, *args, **kwargs) -> Any:
    """
    Esegue una funzione aggiornando l'interfaccia periodicamente.
    Da usare per operazioni lunghe come l'analisi di mercato.

    Args:
        func: La funzione da eseguire
        log_callback: Funzione di callback per il logging (opzionale)
        *args, **kwargs: Argomenti per la funzione
    
    Returns:
        Il risultato finale della funzione
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    try:
        # Esegui la funzione
        result = func(*args, **kwargs)
    
        # Raggruppa gli aggiornamenti del log per evitare troppi aggiornamenti UI
        log_updates = 0
        log(f"⏳ Elaborazione in corso... (aggiornamenti: {log_updates})")
    
        # Esegui la funzione e aggiorna periodicamente il log
        return result
    except Exception as e:
        error_msg = f"Errore durante l'esecuzione: {str(e)}"
        log(error_msg)
        logging.error(error_msg)
        return None  # O un altro valore appropriato