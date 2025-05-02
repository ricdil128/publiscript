import linecache

fname = 'ui/book_builder.py'
start, end = 3480, 3520

print(f"Mostro le righe {start}–{end} di {fname} (spazi mostrati come “·”):\n")
for i in range(start, end + 1):
    line = linecache.getline(fname, i)
    if not line:
        continue
    visible = line.replace(' ', '·').rstrip('\n')
    print(f"{i:4d}: {visible}")