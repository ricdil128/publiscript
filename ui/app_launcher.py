"""
Launcher per l'interfaccia utente Gradio.
"""

import gradio as gr
from .book_builder import AIBookBuilder, apply_debug_patching

def launch_app(server_name="127.0.0.1", server_port=7860, share=False, enable_debug=False):
    """
    Funzione per avviare l'interfaccia Gradio di PubliScript.
    
    Args:
        server_name (str): Nome del server (default: "127.0.0.1")
        server_port (int): Porta del server (default: 7860)
        share (bool): Se True, crea un link pubblico condivisibile (default: False)
        enable_debug (bool): Se True, attiva il debug avanzato per send_to_genspark
        
    Returns:
        gradio.Interface: L'istanza dell'interfaccia Gradio
    """
    print("Avvio dell'applicazione...")
    try:
        print("Creazione builder...")
        builder = AIBookBuilder()
        
        # Applica il patching di debug se richiesto
        if enable_debug:
            try:
                print("Attivazione modalità debug...")
                apply_debug_patching(builder)
                print("✅ Modalità debug attivata con successo")
            except Exception as debug_error:
                print(f"⚠️ Impossibile attivare il debug mode: {str(debug_error)}")
                import traceback
                print("Dettagli errore debug:")
                traceback.print_exc()
        
        print("Creazione interfaccia...")
        interface = builder.create_interface()
        print("Avvio dell'interfaccia...")
        interface.launch(
            server_name=server_name,
            server_port=server_port,
            share=share,
            show_error=True
        )
        return interface
    except Exception as e:
        print(f"ERRORE CRITICO: {str(e)}")
        import traceback
        traceback.print_exc()
        input("Premi Enter per uscire...")
        raise

if __name__ == "__main__":
    launch_app()