#!/usr/bin/env python3
import os
import sys
import argparse

def find_unmatched(file_path, context=3):
    openers = {"if": "if", "try": "try"}
    closers = {"else": ["if", "try"], "elif": ["if"], "except": ["try"], "finally": ["try"]}

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    indent_stack = [0]
    stack = []
    unmatched = []

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip('\n')
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue
        indent = len(line) - len(stripped)

        # pop indents
        while indent < indent_stack[-1]:
            indent_stack.pop()
            if stack: stack.pop()

        tokens = stripped.split()
        # opener
        if tokens[0] in openers and stripped.endswith(':'):
            stack.append((tokens[0], idx))
            indent_stack.append(indent + 4)
        # closer
        elif tokens[0] in closers and stripped.endswith(':'):
            expected = closers[tokens[0]]
            if not stack or stack[-1][0] not in expected:
                unmatched.append((idx, tokens[0]))
            else:
                stack.pop()
                indent_stack.pop()

    # eventuali opener rimasti
    for opener, ln in stack:
        unmatched.append((ln, opener))

    # stampa contesto
    for ln, kind in unmatched:
        start = max(1, ln - context)
        end = min(len(lines), ln + context)
        print(f"\n--- Problema: riga {ln} → “{kind}” non corrisponde ---")
        for i in range(start, end+1):
            prefix = ">>" if i == ln else "  "
            print(f"{prefix} {i:4}: {lines[i-1].rstrip()}")
    if not unmatched:
        print("Nessun if/try/else/except non corrisposto trovato.")

def main():
    parser = argparse.ArgumentParser(
        description="Stampa blocchi if/try aperti o else/except orfani in un file Python"
    )
    parser.add_argument("file", help="Percorso al file Python da controllare")
    parser.add_argument("-c", "--context", type=int, default=3,
                        help="Numero di righe di contesto da mostrare (default: 3)")
    args = parser.parse_args()

    if not os.path.isfile(args.file):
        print(f"Errore: file non trovato → {args.file}")
        sys.exit(1)

    find_unmatched(args.file, context=args.context)

if __name__ == "__main__":
    main()