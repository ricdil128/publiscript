import os
import sys
import argparse

def find_unclosed_blocks(file_path):
    openers = {"if": "if", "try": "try", "for": "for", "while": "while", "with": "with"}
    closers = {"else": ["if", "try"], "elif": ["if"], "except": ["try"], "finally": ["try"]}
    
    stack = []
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    indent_stack = [0]
    
    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip('\n')
        # Salta righe vuote o commenti
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        
        indent = len(line) - len(stripped)
        
        # Dedent: pop fino a indentazione minore o uguale
        while indent < indent_stack[-1]:
            indent_stack.pop()
            if stack: stack.pop()
        
        tokens = stripped.split()
        # Apertura di un blocco
        if tokens[0] in openers and stripped.endswith(':'):
            stack.append((tokens[0], idx))
            indent_stack.append(indent + 4)  # si assume passo indent di 4 spazi
        # Chiusura senza opener
        elif tokens[0] in closers and stripped.endswith(':'):
            expected = closers[tokens[0]]
            if not stack or stack[-1][0] not in expected:
                issues.append(f"Line {idx}: '{tokens[0]}' without matching opener (expected one of {expected})")
            else:
                # corrisponde, poppa l'opener
                stack.pop()
                indent_stack.pop()
    
    # Qualsiasi opener rimasto non è stato chiuso
    for opener, line_no in stack:
        issues.append(f"Line {line_no}: '{opener}' block not closed")
        
    return issues

def main():
    parser = argparse.ArgumentParser(description="Detect unclosed try/except and if/else blocks in a Python file")
    parser.add_argument("file", help="Path to the Python file to analyze")
    args = parser.parse_args()
    
    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)
    
    issues = find_unclosed_blocks(args.file)
    if issues:
        print("Found unclosed or unmatched blocks:")
        for issue in issues:
            print(" -", issue)
        sys.exit(1)
    else:
        print("No unclosed or unmatched try/except/if/else blocks found.")

if __name__ == "__main__":
    main()