# test_create_interface.py
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
    lines = f.readlines()

# Trova la posizione del metodo create_interface
create_interface_line = None
for i, line in enumerate(lines):
    if "def create_interface" in line:
        create_interface_line = i
        break

if create_interface_line is not None:
    print(f"Metodo create_interface trovato alla riga {create_interface_line + 1}")
    
    # Analizziamo le righe precedenti
    start_context = max(0, create_interface_line - 10)
    end_context = min(len(lines), create_interface_line + 10)
    
    print(f"\nContesto ({start_context+1}-{end_context+1}):")
    for i in range(start_context, end_context):
        line = lines[i].rstrip()
        line_marker = "→" if i == create_interface_line else " "
        print(f"{i+1:5d} {line_marker} {line}")
    
    # Analizziamo la struttura delle parentesi e virgolette
    method_content = "".join(lines[create_interface_line:])
    
    # Conteggio caratteri speciali
    paren_open = method_content.count("(")
    paren_close = method_content.count(")")
    brace_open = method_content.count("{")
    brace_close = method_content.count("}")
    bracket_open = method_content.count("[")
    bracket_close = method_content.count("]")
    quotes_double = method_content.count("\"")
    quotes_triple = method_content.count("\"\"\"")
    
    print(f"\nAnalisi dei bilanciamenti:")
    print(f"Parentesi tonde:   {paren_open} aperte, {paren_close} chiuse {'✅' if paren_open == paren_close else '❌'}")
    print(f"Parentesi graffe:  {brace_open} aperte, {brace_close} chiuse {'✅' if brace_open == brace_close else '❌'}")
    print(f"Parentesi quadre:  {bracket_open} aperte, {bracket_close} chiuse {'✅' if bracket_open == bracket_close else '❌'}")
    print(f"Virgolette doppie: {quotes_double} {'✅' if quotes_double % 2 == 0 else '❌'}")
    print(f"Triple virgolette: {quotes_triple} {'✅' if quotes_triple % 2 == 0 else '❌'}")
else:
    print("❌ Metodo create_interface non trovato nel file")