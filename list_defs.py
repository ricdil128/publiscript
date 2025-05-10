import re

with open("book_builder.py", encoding="utf-8") as f:
    for lineno, line in enumerate(f, 1):
        m = re.match(r'^\s*def\s+(\w+)\s*\(', line)
        if m:
            print(f"{lineno:4d}: {m.group(1)}")
