# generators/common_generator.py

import os
import traceback
from framework.book_generator import generate_book as generate_book_func
from ai_interfaces.genspark_driver import send_to_genspark

def generate_book(self, book_title, book_language, voice_style, book_index):
    """
    Genera il libro utilizzando i dati dell'interfaccia e i dati CRISP disponibili.
    Ora delega alla funzione nel modulo framework/book_generator.py
    """
    # Ottieni il tipo di libro (se disponibile)
    book_type = None
    if hasattr(self, 'book_type_hidden'):
        book_type = self.book_type_hidden.value

    # Delega la generazione alla funzione nel modulo book_generator
    result = generate_book_func(
        book_title=book_title,
        book_language=book_language,
        voice_style=voice_style,
        book_index=book_index,
        driver=self.driver,
        chat_manager=self.chat_manager,
        current_analysis=self.current_analysis,
        book_type_hidden=book_type,
        send_to_genspark=send_to_genspark
    )

    self.add_log(f"Risultato generazione libro: {result}")
    return self.chat_manager.get_log_history_string()
