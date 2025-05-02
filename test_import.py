# test_import.py
import sys
from ui.book_builder import AIBookBuilder

# Stampa il percorso del modulo caricato
print(f"book_builder.py caricato da: {sys.modules['ui.book_builder'].__file__}")

# Crea un'istanza e verifica i metodi
builder = AIBookBuilder()
print(f"Metodi disponibili: {[m for m in dir(builder) if not m.startswith('_')]}")