# find_unbalanced_parentheses.py
import re
import os
import sys

def find_unbalanced_parentheses(file_path, start_line=None, end_line=None):
    """
    Analizza un file Python per trovare parentesi non bilanciate.
    Opzionalmente puoi specificare un intervallo di righe da analizzare.
    
    Args:
        file_path: Percorso del file da analizzare
        start_line: Riga di inizio (opzionale)
        end_line: Riga di fine (opzionale)
    """
    # Leggi il file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()
    
    # Imposta l'intervallo di righe da analizzare
    if start_line is None:
        start_line = 0
    else:
        start_line = max(0, start_line - 1)  # Converte in indice zero-based
    
    if end_line is None:
        end_line = len(lines)
    else:
        end_line = min(len(lines), end_line)
    
    # Seleziona solo le righe dell'intervallo specificato
    lines_to_analyze = lines[start_line:end_line]
    content_to_analyze = "\n".join(lines_to_analyze)
    
    print(f"Analisi delle righe {start_line+1}-{end_line} su {len(lines)} totali")
    
    # Crea un dizionario per le posizioni dei caratteri
    char_positions = {}
    line_number = start_line + 1
    char_index = 0
    
    for i, line in enumerate(lines_to_analyze):
        for j, char in enumerate(line):
            char_positions[char_index] = (line_number, j+1)
            char_index += 1
        char_index += 1  # Per il newline
        line_number += 1
    
    # Inizializza stack per ogni tipo di parentesi
    stack_round = []    # Per ()
    stack_square = []   # Per []
    stack_curly = []    # Per {}
    stack_triple_quote = []  # Per """
    
    # Per saltare il contenuto delle stringhe
    in_string = False
    string_start = None
    
    # Per tenere traccia dei problemi trovati
    problems = []
    
    # Analizza il contenuto carattere per carattere
    i = 0
    while i < len(content_to_analyze):
        char = content_to_analyze[i]
        
        # Gestione stringhe con triple virgolette
        if i + 2 < len(content_to_analyze) and content_to_analyze[i:i+3] == '"""':
            if not stack_triple_quote:  # Apertura stringa
                stack_triple_quote.append(i)
                in_string = True
            else:  # Chiusura stringa
                stack_triple_quote.pop()
                if not stack_triple_quote:
                    in_string = False
            i += 3
            continue
        
        # Ignora i caratteri all'interno delle stringhe (eccetto """)
        if in_string:
            i += 1
            continue
        
        # Gestione singoli caratteri di parentesi
        if char == '(':
            stack_round.append(i)
        elif char == ')':
            if stack_round:
                stack_round.pop()
            else:
                # Parentesi chiusa senza corrispondente apertura
                line, col = char_positions.get(i, (0, 0))
                problems.append(f"Parentesi tonda chiusa ')', trovata senza apertura alla riga {line}, colonna {col}")
        
        elif char == '[':
            stack_square.append(i)
        elif char == ']':
            if stack_square:
                stack_square.pop()
            else:
                # Parentesi quadra chiusa senza corrispondente apertura
                line, col = char_positions.get(i, (0, 0))
                problems.append(f"Parentesi quadra chiusa ']', trovata senza apertura alla riga {line}, colonna {col}")
        
        elif char == '{':
            stack_curly.append(i)
        elif char == '}':
            if stack_curly:
                stack_curly.pop()
            else:
                # Parentesi graffa chiusa senza corrispondente apertura
                line, col = char_positions.get(i, (0, 0))
                problems.append(f"Parentesi graffa chiusa '}}', trovata senza apertura alla riga {line}, colonna {col}")
        
        i += 1
    
    # Verifica se ci sono parentesi aperte non chiuse
    for i in stack_round:
        line, col = char_positions.get(i, (0, 0))
        problems.append(f"Parentesi tonda aperta '(' alla riga {line}, colonna {col} non è mai chiusa")
    
    for i in stack_square:
        line, col = char_positions.get(i, (0, 0))
        problems.append(f"Parentesi quadra aperta '[' alla riga {line}, colonna {col} non è mai chiusa")
    
    for i in stack_curly:
        line, col = char_positions.get(i, (0, 0))
        problems.append(f"Parentesi graffa aperta '{{' alla riga {line}, colonna {col} non è mai chiusa")
    
    for i in stack_triple_quote:
        line, col = char_positions.get(i, (0, 0))
        problems.append(f"Triple virgolette aperte '\"\"\"' alla riga {line}, colonna {col} non sono mai chiuse")
    
    # Stampa i risultati
    if problems:
        print(f"\nProblemi trovati: {len(problems)}")
        for problem in problems:
            print(f"- {problem}")
    else:
        print("\n✅ Nessun problema di parentesi trovato!")
    
    # Stampa un riepilogo dello stato
    print(f"\nRiepilogo bilanciamento:")
    print(f"- Parentesi tonde: {len(stack_round)} aperte non chiuse, {len([p for p in problems if 'tonda chiusa' in p])} chiuse senza apertura")
    print(f"- Parentesi quadre: {len(stack_square)} aperte non chiuse, {len([p for p in problems if 'quadra chiusa' in p])} chiuse senza apertura")
    print(f"- Parentesi graffe: {len(stack_curly)} aperte non chiuse, {len([p for p in problems if 'graffa chiusa' in p])} chiuse senza apertura")
    print(f"- Triple virgolette: {len(stack_triple_quote)} non chiuse")
    
    return problems

if __name__ == "__main__":
    # Ottieni i parametri da riga di comando
    file_path = None
    start_line = None
    end_line = None
    
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
    else:
        file_path = os.path.join("ui", "book_builder.py")  # Default
    
    if len(sys.argv) >= 3:
        start_line = int(sys.argv[2])
    
    if len(sys.argv) >= 4:
        end_line = int(sys.argv[3])
    
    print(f"Analisi del file: {file_path}")
    find_unbalanced_parentheses(file_path, start_line, end_line)