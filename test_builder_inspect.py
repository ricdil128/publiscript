# test_builder_inspect.py
import inspect
import sys
import os

# Stampa alcune informazioni iniziali
print(f"Python: {sys.version}")
print(f"Percorso corrente: {os.getcwd()}")

# Importa la classe
try:
    from ui.book_builder import AIBookBuilder
    print("✅ Importazione AIBookBuilder riuscita")
except Exception as e:
    print(f"❌ Errore di importazione: {str(e)}")
    sys.exit(1)

# Esamina il modulo
module = sys.modules['ui.book_builder']
print(f"\nFile del modulo: {module.__file__}")
print(f"Ultimo modificato: {os.path.getmtime(module.__file__)}")

# Esamina la classe
print(f"\n--- CLASSE ---")
print(f"Classe: {AIBookBuilder}")
print(f"Dir classe: {dir(AIBookBuilder)}")
print(f"Metodi pubblici: {[m for m in dir(AIBookBuilder) if not m.startswith('_')]}")
print(f"Attributi classe: {AIBookBuilder.__dict__.keys()}")

# Verifica se create_interface è nella classe
print(f"\n--- VERIFICA create_interface NELLA CLASSE ---")
print(f"'create_interface' in dir(AIBookBuilder): {'create_interface' in dir(AIBookBuilder)}")
print(f"'create_interface' in AIBookBuilder.__dict__: {'create_interface' in AIBookBuilder.__dict__}")

# Crea un'istanza
print(f"\n--- ISTANZA ---")
try:
    builder = AIBookBuilder()
    print(f"Instance: {builder}")
    print(f"Dir istanza: {dir(builder)}")
    print(f"Metodi pubblici istanza: {[m for m in dir(builder) if not m.startswith('_')]}")
    print(f"Attributi istanza: {builder.__dict__.keys()}")
except Exception as e:
    print(f"❌ Errore creazione istanza: {str(e)}")

# Verifica se create_interface è nell'istanza
print(f"\n--- VERIFICA create_interface NELL'ISTANZA ---")
print(f"'create_interface' in dir(builder): {'create_interface' in dir(builder)}")
print(f"hasattr(builder, 'create_interface'): {hasattr(builder, 'create_interface')}")
print(f"getattr(builder, 'create_interface', None): {getattr(builder, 'create_interface', None)}")

# Ottieni il codice sorgente
print(f"\n--- SORGENTE ---")
try:
    source = inspect.getsource(AIBookBuilder)
    print(f"Primi 200 caratteri:\n{source[:200]}...\n")
except Exception as e:
    print(f"Errore nel recupero sorgente: {str(e)}")

# Cerca definizoini di create_interface nel file
print(f"\n--- RICERCA create_interface NEL FILE ---")
try:
    with open(module.__file__, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Cerca tutte le occorrenze di "def create_interface"
    import re
    matches = re.findall(r"def\s+create_interface", content)
    print(f"Occorrenze di 'def create_interface': {len(matches)}")
    
    # Cerca con indentazione
    matches_indented = re.findall(r"    def\s+create_interface", content)
    print(f"Occorrenze di '    def create_interface': {len(matches_indented)}")
    
    # Cerca il contesto
    for i, line in enumerate(content.split("\n")):
        if "def create_interface" in line:
            start = max(0, i-5)
            end = min(i+5, len(content.split("\n")))
            context = "\n".join(content.split("\n")[start:end])
            print(f"Contesto (righe {start}-{end}):\n{context}")
except Exception as e:
    print(f"Errore nell'analisi del file: {str(e)}")