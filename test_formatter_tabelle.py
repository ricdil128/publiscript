import webbrowser
from framework.formatters import format_analysis_results_html

# Dati di test
keyword = "test_tabella"
market = "USA"
book_type = "Manuale"
language = "Italiano"
analysis_type = "CRISP"

# Simula un contesto con tabella markdown
markdown_con_tabella = """
=== Analisi test_tabella - 20250509_120000 ===
| Criterio | Valore 1 | Valore 2 |
|----------|----------|----------|
| Primo    | A        | B        |
| Secondo  | C        | D        |
"""

# Crea il file context.txt
with open("context.txt", "w", encoding="utf-8") as f:
    f.write(markdown_con_tabella)

# Genera l'HTML
html_output = format_analysis_results_html(
    keyword=keyword,
    market=market,
    book_type=book_type,
    language=language,
    context=None,
    save_to_file=False,
    analysis_type=analysis_type
)

# Salva il file
output_file = "test_output_tabelle.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_output)

# Apri nel browser
webbrowser.open(f"file:///{output_file}")
print(f"✅ File salvato in: {output_file}")
