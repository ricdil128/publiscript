# generators/crisp_generator.py

import os
import traceback
from datetime import datetime

from framework.book_generator import generate_book_crisp

def _generate_book_crisp(self, book_title, book_language, voice_style, book_index, params=None, analysis_context=None):
        """
        Genera il libro usando il framework CRISP 5.0.
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
        from framework.book_generator import generate_book_crisp
    
        try:
            # Logga info sui parametri aggiuntivi (che saranno ignorati nella chiamata)
            if params:
                param_keys = list(params.keys())
                self.add_log(f"📝 Nota: Parametri aggiuntivi disponibili ma non utilizzati nel modulo esterno: {param_keys}")
        
            if analysis_context:
                self.add_log(f"📝 Nota: Contesto analisi disponibile ({len(analysis_context)} caratteri) ma non utilizzato nel modulo esterno")
            
                # Come soluzione temporanea, salviamo il contesto in un file che potrebbe essere utilizzato
                # dal modulo esterno se implementato per cercarlo
                try:
                    import os
                    from datetime import datetime
                
                    os.makedirs("temp", exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    context_file = f"temp/analysis_context_{timestamp}.txt"
                
                    with open(context_file, "w", encoding="utf-8") as f:
                        f.write(analysis_context)
                    
                    self.add_log(f"📄 Contesto dell'analisi salvato in: {context_file}")
                
                    # Estendi current_analysis con il percorso al file del contesto
                    if hasattr(self, 'current_analysis') and self.current_analysis:
                        self.current_analysis['analysis_context_file'] = context_file
                except Exception as ctx_error:
                    self.add_log(f"⚠️ Impossibile salvare il contesto: {str(ctx_error)}")
        
            # Chiama la funzione nel modulo esterno con i parametri standard
            result = generate_book_crisp(
                book_title, 
                book_language, 
                voice_style, 
                book_index,
                crisp_framework=self.crisp,
                driver=self.driver,
                chat_manager=self.chat_manager,
                current_analysis=self.current_analysis
            )
    
            # Il risultato potrebbe essere il percorso del libro o un messaggio di errore
            if result and not result.startswith("Errore:"):
                self.add_log(f"📚 Libro generato con successo: {result}")
            else:
                self.add_log(f"❌ {result}")
            
        except Exception as e:
            self.add_log(f"❌ Errore durante la generazione del libro: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
    
        return self.chat_manager.get_log_history_string()