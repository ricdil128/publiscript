import textwrap

# apri il file originale
with open("dede.py", encoding="utf-8") as f:
    content = f.read()

# rimuove l’indentazione comune
dedented = textwrap.dedent(content)

# sovrascrive il file
with open("dede.py", "w", encoding="utf-8") as f:
    f.write(dedented)

print("dede.py dedented correttamente")