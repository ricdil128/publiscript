"""
Utilities per l'interfaccia utente: aggiornamenti di stato, feedback e componenti UI.
"""

import logging
from typing import Optional, Union, Dict, List, Any

def update_analysis_status(analysis_status, status_text: str, progress_percentage: Optional[int] = None, log_callback=None):
    """
    Aggiorna lo stato dell'analisi nell'interfaccia.

    Args:
        analysis_status: Componente UI per lo stato dell'analisi
        status_text: Testo dello stato
        progress_percentage: Percentuale di completamento (opzionale)
        log_callback: Funzione di callback per il logging (opzionale)
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    try:
        if analysis_status:
            if progress_percentage is not None:
                status_html = f"""
                <div class="status-container">
                    <div class="status-text mb-2"><strong>Stato:</strong> {status_text}</div>
                    <div class="progress-bar-container bg-gray-200 rounded-full h-4 w-full">
                        <div class="progress-bar bg-blue-600 h-4 rounded-full" style="width: {progress_percentage}%;"></div>
                    </div>
                    <div class="text-right text-sm text-gray-500">{progress_percentage}%</div>
                </div>
                """
            else:
                status_html = f"<div class='status-text'><strong>Stato:</strong> {status_text}</div>"
            
            analysis_status.update(value=status_html)
            log(f"📊 Stato analisi aggiornato: {status_text}")
        else:
            log(f"⚠️ Componente status non disponibile")
    except Exception as e:
        log(f"⚠️ Errore nell'aggiornamento dello stato: {str(e)}")

def show_feedback(results_display, title: str, message: str, type: str = "info", log_callback=None):
    """
    Mostra un messaggio di feedback all'utente.

    Args:
        results_display: Componente UI per visualizzare i risultati
        title: Titolo del messaggio
        message: Testo del messaggio
        type: Tipo di messaggio (info, success, warning, error)
        log_callback: Funzione di callback per il logging (opzionale)
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        # Determina il colore in base al tipo
        color_class = {
            "info": "blue",
            "success": "green",
            "warning": "yellow",
            "error": "red"
        }.get(type, "blue")
    
        feedback_html = f"""
        <div class="bg-{color_class}-50 border-l-4 border-{color_class}-500 p-4 mb-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-{color_class}-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-{color_class}-800 font-medium">{title}</h3>
                    <div class="mt-2 text-{color_class}-700">
                        <p>{message}</p>
                    </div>
                </div>
            </div>
        </div>
        """
    
        # Aggiorna l'interfaccia appropriata
        if results_display:
            current_value = results_display.value or ""
            results_display.update(value=feedback_html + current_value)
    
        log(f"💬 Feedback mostrato: {title}")
    except Exception as e:
        log(f"⚠️ Errore nella visualizzazione del feedback: {str(e)}")

def debug_check_components(components: Dict[str, Any], log_callback=None):
    """
    Controlla che i componenti UI siano disponibili e funzionanti.
    
    Args:
        components: Dizionario dei componenti da controllare
        log_callback: Funzione di callback per il logging (opzionale)
        
    Returns:
        bool: True se tutti i componenti sono OK, False altrimenti
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
            
    try:
        all_ok = True
        for name, component in components.items():
            if component is None:
                log(f"❌ Componente mancante: {name}")
                all_ok = False
            else:
                log(f"✅ Componente OK: {name}")
                
        return all_ok
    except Exception as e:
        log(f"❌ Errore nel check dei componenti: {str(e)}")
        return False