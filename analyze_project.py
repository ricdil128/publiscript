# analyze_project.py
import os
import re
import sys

def analyze_project(root_dir='.'):
    """Analizza la struttura del progetto Python."""
    modules = {}
    functions = {}
    imports = {}
    
    # Pattern per trovare definizioni di funzioni e import
    func_pattern = re.compile(r'def\s+([a-zA-Z0-9_]+)\s*\(')
    import_pattern = re.compile(r'(?:from\s+([a-zA-Z0-9_.]+)\s+import)|(?:import\s+([a-zA-Z0-9_., ]+))')
    
    # Cerca tutti i file Python
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                module_name = os.path.splitext(filename)[0]
                module_path = os.path.relpath(filepath, root_dir)
                
                # Leggi il contenuto del file
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Trova tutte le definizioni di funzioni
                funcs = func_pattern.findall(content)
                if funcs:
                    modules[module_path] = funcs
                    for func in funcs:
                        functions[func] = module_path
                
                # Trova tutti gli import
                module_imports = []
                for match in import_pattern.finditer(content):
                    imported = match.group(1) or match.group(2)
                    if imported:
                        for imp in imported.split(','):
                            module_imports.append(imp.strip())
                
                if module_imports:
                    imports[module_path] = module_imports
    
    return modules, functions, imports

if __name__ == '__main__':
    modules, functions, imports = analyze_project()
    
    print("=== STRUTTURA DEI MODULI ===")
    for module, funcs in modules.items():
        print(f"\nModulo: {module}")
        for func in funcs:
            print(f"  - {func}()")
    
    print("\n\n=== DEFINIZIONI DI FUNZIONI ===")
    for func, module in functions.items():
        print(f"{func}() -> {module}")
    
    print("\n\n=== DIPENDENZE (IMPORT) ===")
    for module, imported in imports.items():
        print(f"\nModulo: {module} importa:")
        for imp in imported:
            print(f"  - {imp}")