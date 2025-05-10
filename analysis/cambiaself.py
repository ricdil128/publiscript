import re

# Elenca qui i metodi/attributi di AIBookBuilder che vuoi spostare su builder.*
builder_methods = [
    "add_log",
    "check_existing_analysis",
    "load_project_details",
    "ripristina_analisi_da_database",
    "continue_analysis",
    "resume_analysis",
    "complete_analysis",
    "export_project",
    "update_project_count",
    "delete_project",
    "search_projects",
    "get_database_stats",
    # aggiungi qui eventuali altri metodi che chiami su self.
]

# Compila un pattern che cerchi solo self.<metodo>(
pattern = re.compile(r"\bself\.(" + "|".join(builder_methods) + r")\(")

# Leggi il file
with open("analyzers.py", "r", encoding="utf-8") as f:
    code = f.read()

# Fai la sostituzione
new_code = pattern.sub(r"builder.\1(", code)

# (Facoltativo) salva in un nuovo file per sicurezza
with open("analyzers_refactored.py", "w", encoding="utf-8") as f:
    f.write(new_code)

print("Refactoring completato: vedi analyzers_refactored.py")
