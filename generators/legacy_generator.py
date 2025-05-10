# generators/legacy_generator.py

import os
import traceback

def _generate_book_legacy(self, book_title, book_language, voice_style, book_index, params=None, analysis_context=None):
    """
    Metodo legacy per generare il libro.
    Ora delega alla funzione in framework/book_generator.py

    Args:
        book_title: Titolo del libro
        book_language: Lingua del libro
        voice_style: Stile narrativo
        book_index: Indice del libro
        params: Parametri aggiuntivi (ignorati nella versione delegata)
        analysis_context: Contesto dell'analisi (ignorato nella versione delegata)

    Returns:
        str: Log dell'operazione
    """
    from framework.book_generator import generate_book_legacy

    try:
        # Logga info sui parametri aggiuntivi (che saranno ignorati nella chiamata)
        if params:
            param_keys = list(params.keys())
            self.add_log(f"📝 Nota: Parametri aggiuntivi disponibili ma non utilizzati: {param_keys}")

        if analysis_context:
            self.add_log(f"📝 Nota: Contesto analisi disponibile ({len(analysis_context)} caratteri) ma non usato")

            # Aggiungilo al file context.txt se esiste
            try:
                if os.path.exists("context.txt"):
                    with open("context.txt", "a", encoding="utf-8") as f:
                        f.write("\n\n=== CONTESTO AGGIUNTIVO PER LIBRO ===\n\n")
                        f.write(analysis_context)
                    self.add_log("📄 Contesto aggiunto al file context.txt")
            except Exception as ctx_error:
                self.add_log(f"⚠️ Impossibile aggiungere contesto: {ctx_error}")

        # Chiama il generatore legacy
        result = generate_book_legacy(
            book_title,
            book_language,
            voice_style,
            book_index,
            driver=self.driver,
            chat_manager=self.chat_manager
        )
        self.add_log(f"📚 Libro legacy generato: {result}")

    except Exception as e:
        self.add_log(f"❌ Errore during book generation: {e}")
        self.add_log(traceback.format_exc())

    return self.chat_manager.get_log_history_string()
