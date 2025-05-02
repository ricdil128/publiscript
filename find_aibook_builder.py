# find_aibook_builder.py
import os
import sys
from pathlib import Path

def find_class_in_files(class_name, root_dir='.', extensions=['.py']):
    """Trova i file che contengono una determinata classe"""
    root_path = Path(root_dir)
    found_files = []
    
    for path in root_path.rglob('*'):
        if path.suffix in extensions and path.is_file():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if f"class {class_name}" in content:
                        found_files.append(str(path))
                        print(f"Trovato '{class_name}' in: {path}")
            except Exception as e:
                print(f"Errore leggendo {path}: {e}")
    
    return found_files

if __name__ == "__main__":
    print("Sto cercando la classe AIBookBuilder...")
    files = find_class_in_files("AIBookBuilder")
    
    if not files:
        print("Nessun file trovato contenente 'class AIBookBuilder'")
        # Cerchiamo file che potrebbero contenere la classe in modo parziale
        print("Sto cercando file che potrebbero contenere riferimenti a AIBookBuilder...")
        partial_files = find_class_in_files("BookBuilder") + find_class_in_files("Builder")
        
        if partial_files:
            print(f"Trovati {len(partial_files)} file che potrebbero contenere riferimenti:")
            for file in partial_files:
                print(f" - {file}")
        else:
            print("Nessun riferimento trovato")
    else:
        print(f"Trovati {len(files)} file:")
        for file in files:
            print(f" - {file}")