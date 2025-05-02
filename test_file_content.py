# test_file_content.py
import os
import re

# Percorso del file
file_path = os.path.join("ui", "book_builder.py")

# Verifica che il file esista
if not os.path.exists(file_path):
    print(f"❌ File non trovato: {file_path}")
    exit(1)

# Leggi il contenuto del file
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Stampa alcune statistiche
print(f"Dimensione file: {len(content)} caratteri")
# Per contare le righe, usiamo len() invece di count('\n')
lines = content.splitlines()
print(f"Numero di righe: {len(lines)}")

# Cerca la classe AIBookBuilder
class_pattern = r"class\s+AIBookBuilder\s*:"
class_matches = re.findall(class_pattern, content)
print(f"\nDefinizioni della classe AIBookBuilder trovate: {len(class_matches)}")

# Cerca il metodo create_interface
method_pattern = r"def\s+create_interface\s*\("
method_matches = re.findall(method_pattern, content)
print(f"Definizioni del metodo create_interface trovate: {len(method_matches)}")

# Cerca il metodo con indentazione
indented_pattern = r"    def\s+create_interface\s*\("
indented_matches = re.findall(indented_pattern, content)
print(f"Definizioni indentate del metodo create_interface: {len(indented_matches)}")

# Trova la posizione della classe
class_positions = [match.start() for match in re.finditer(class_pattern, content)]
method_positions = [match.start() for match in re.finditer(method_pattern, content)]

if class_positions and method_positions:
    print(f"\nPosizione della classe: {class_positions[0]}")
    print(f"Posizione del metodo: {method_positions[0]}")
    
    if method_positions[0] > class_positions[0]:
        print("✅ Il metodo è definito dopo l'inizio della classe")
        
        # Controlla se ci sono definizioni di classe dopo il metodo
        class_after_method = [pos for pos in class_positions if pos > method_positions[0]]
        if class_after_method:
            print(f"⚠️ C'è un'altra definizione di classe dopo il metodo: posizione {class_after_method[0]}")
    else:
        print("❌ Il metodo è definito PRIMA dell'inizio della classe")

# Cerca la struttura completa
print("\nAnalisi delle strutture:")
# Trova le linee della classe e del metodo
lines = content.splitlines()
class_lines = [i for i, line in enumerate(lines) if re.match(class_pattern, line)]
method_lines = [i for i, line in enumerate(lines) if re.match(r"\s*def\s+create_interface\s*\(", line)]

if class_lines and method_lines:
    print(f"Classe definita alla riga: {class_lines[0] + 1}")
    for method_line in method_lines:
        print(f"Metodo create_interface trovato alla riga: {method_line + 1}")
        # Controlla l'indentazione
        if method_line < len(lines):
            method_text = lines[method_line]
            indent = len(method_text) - len(method_text.lstrip())
            print(f"Indentazione: {indent} spazi")
            if indent == 4:
                print("✅ Indentazione corretta (4 spazi)")
            else:
                print(f"❌ Indentazione ERRATA ({indent} spazi invece di 4)")