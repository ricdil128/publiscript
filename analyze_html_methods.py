"""
Script di diagnostica HTML semplificato per PubliScript.
Questo script si concentra sul flusso della generazione HTML e sui metodi coinvolti.
"""
import os
import re
import importlib.util

def load_module(file_path):
    """Carica un modulo Python da un file"""
    try:
        module_name = os.path.basename(file_path).replace('.py', '')
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None
    except Exception as e:
        print(f"Errore nel caricare {file_path}: {str(e)}")
        return None

def analyze_html_flow(directory='.'):
    """Analizza il flusso di generazione HTML"""
    print("=== ANALISI DEL FLUSSO HTML ===")
    
    # File principali da analizzare
    main_files = [
        os.path.join('ui', 'book_builder.py'),
        os.path.join('framework', 'formatters.py'),
        os.path.join('analysis', 'analyzers.py')
    ]
    
    # Metodi chiave nella generazione HTML
    key_methods = [
        'save_response_to_project',
        '_generate_html_from_context_file',
        '_process_section_content',
        'process_table_html',
        '_generate_styled_html',
        'save_analysis_to_html',
        'format_analysis_results_html'
    ]
    
    # Mappa i file ai loro percorsi completi
    file_paths = {}
    for main_file in main_files:
        path = os.path.join(directory, main_file)
        if os.path.exists(path):
            file_paths[main_file] = path
        else:
            print(f"⚠️ File non trovato: {path}")
    
    # Analisi dei file
    method_definitions = {}
    method_calls = {}
    
    for file_name, file_path in file_paths.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            print(f"\n📄 Analisi di {file_name}:")
            
            # Trova definizioni dei metodi chiave
            for method in key_methods:
                method_pattern = fr'def\s+{method}\s*\((.*?)\):'
                matches = list(re.finditer(method_pattern, content, re.DOTALL))
                
                if matches:
                    method_definitions[method] = {
                        'file': file_name,
                        'count': len(matches)
                    }
                    print(f"  ✓ Metodo '{method}' definito {len(matches)} volta/e")
                    
                    # Trova il corpo del metodo per il primo match
                    match = matches[0]
                    start_pos = match.end()
                    
                    # Trova l'indentazione del metodo
                    next_line = content[start_pos:].split('\n', 1)[1] if '\n' in content[start_pos:] else ""
                    base_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Estrai il corpo del metodo
                    lines = content[start_pos:].split('\n')
                    method_body = []
                    for line in lines[1:]:  # Salta la riga della firma del metodo
                        if not line.strip():
                            method_body.append(line)
                            continue
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= base_indent and line.strip():
                            break
                        method_body.append(line)
                    
                    method_content = '\n'.join(method_body)
                    
                    # Cerca chiamate ad altri metodi chiave
                    calls_in_method = []
                    for other_method in key_methods:
                        if other_method == method:
                            continue  # Salta se è lo stesso metodo
                        
                        # Cerca chiamate
                        call_pattern = fr'(?:self\.)?{other_method}\('
                        call_matches = list(re.finditer(call_pattern, method_content))
                        
                        if call_matches:
                            for call_match in call_matches:
                                # Prendi un po' di contesto
                                start = max(0, call_match.start() - 40)
                                end = min(len(method_content), call_match.end() + 60)
                                context = method_content[start:end].replace('\n', ' ').strip()
                                
                                calls_in_method.append({
                                    'called_method': other_method,
                                    'context': context
                                })
                    
                    if calls_in_method:
                        method_calls[method] = calls_in_method
                        print(f"    - Chiama: {', '.join(c['called_method'] for c in calls_in_method)}")
            
            # Cerca dove vengono chiamati i metodi chiave
            for method in key_methods:
                # Cerca chiamate al metodo
                call_pattern = fr'(?:self\.)?{method}\('
                call_matches = list(re.finditer(call_pattern, content))
                if call_matches:
                    if method not in method_calls:
                        method_calls[method] = []
                    for call_match in call_matches:
                        # Trova il contesto della chiamata
                        context_start = max(0, call_match.start() - 200)
                        # Cerca l'inizio della funzione che contiene questa chiamata
                        context_content = content[context_start:call_match.start()]
                        method_def_match = re.search(r'def\s+(\w+)\s*\(', context_content[::-1])
                        caller_method = method_def_match.group(1)[::-1] if method_def_match else "unknown"
                        
                        if caller_method != method:  # Evita di registrare chiamate ricorsive
                            print(f"  • Il metodo '{method}' è chiamato da '{caller_method}'")
        
        except Exception as e:
            print(f"❌ Errore nell'analisi di {file_name}: {str(e)}")
    
    # Costruisci il grafo delle chiamate
    print("\n=== GRAFO DELLE CHIAMATE ===")
    print("Ordine di esecuzione (dalla catena di chiamate):")
    
    def print_call_chain(method, depth=0, visited=None):
        if visited is None:
            visited = set()
        
        if method in visited:
            print("  " * depth + f"↻ {method} (loop detected)")
            return
        
        visited.add(method)
        prefix = "  " * depth
        print(f"{prefix}→ {method}")
        
        if method in method_calls:
            for call in method_calls[method]:
                print_call_chain(call['called_method'], depth + 1, visited.copy())
    
    # Inizia dalla radice del flusso
    entry_points = ['save_response_to_project', '_generate_html_from_context_file']
    for entry_point in entry_points:
        if entry_point in method_definitions:
            print(f"\nFlusso da {entry_point}:")
            print_call_chain(entry_point)

def dump_method_source(file_path, method_name):
    """Estrae il codice sorgente di un metodo specifico"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Trova la definizione del metodo
        method_pattern = fr'def\s+{method_name}\s*\((.*?)\):'
        match = re.search(method_pattern, content, re.DOTALL)
        
        if match:
            start_pos = match.start()
            
            # Trova la fine del metodo (cercando la prossima definizione allo stesso livello)
            lines = content[start_pos:].split('\n')
            sig_indent = len(lines[0]) - len(lines[0].lstrip())
            
            method_body = [lines[0]]
            for line in lines[1:]:
                if not line.strip():
                    method_body.append(line)
                    continue
                    
                curr_indent = len(line) - len(line.lstrip())
                if curr_indent <= sig_indent and line.strip() and line.lstrip().startswith('def '):
                    break
                    
                method_body.append(line)
            
            return '\n'.join(method_body)
        else:
            return f"Metodo {method_name} non trovato in {file_path}"
    except Exception as e:
        return f"Errore nell'estrazione del metodo {method_name} da {file_path}: {str(e)}"

def test_debug_process_table_html(project_dir='.'):
    """Test diagnostico della funzione process_table_html"""
    print("\n=== TEST DIAGNOSTICO process_table_html ===")
    
    # Definisci percorsi dei file
    book_builder_path = os.path.join(project_dir, 'ui', 'book_builder.py')
    formatters_path = os.path.join(project_dir, 'framework', 'formatters.py')
    
    # Test 1: Controlla l'esistenza dei file
    book_builder_exists = os.path.exists(book_builder_path)
    formatters_exists = os.path.exists(formatters_path)
    
    print(f"File book_builder.py esistente: {'✓' if book_builder_exists else '✗'}")
    print(f"File formatters.py esistente: {'✓' if formatters_exists else '✗'}")
    
    if not book_builder_exists or not formatters_exists:
        return
    
    # Test 2: Estrai il codice sorgente
    bb_method = dump_method_source(book_builder_path, 'process_table_html')
    fmt_method = dump_method_source(formatters_path, 'process_table_html')
    
    print("\nCodice in book_builder.py:")
    print("-" * 50)
    print(bb_method)
    print("-" * 50)
    
    print("\nCodice in formatters.py:")
    print("-" * 50)
    print(fmt_method)
    print("-" * 50)
    
    # Test 3: Verifica se il metodo in book_builder.py importa correttamente
    if "from framework.formatters import process_table_html" in bb_method:
        print("✓ book_builder.py importa correttamente process_table_html da formatters.py")
    else:
        print("✗ book_builder.py NON importa correttamente process_table_html")
    
    # Test 4: Test diretto della funzione
    print("\nTest diretto di process_table_html:")
    
    # Tabella markdown di test
    test_table = """
| Criterio | Valore 1 | Valore 2 |
|---------|---------|---------|
| Primo | A | B |
| Secondo | C | D |
"""
    
    # Tenta di caricare e usare la funzione
    try:
        # Carica il modulo formatters
        formatters_module = load_module(formatters_path)
        if formatters_module and hasattr(formatters_module, 'process_table_html'):
            # Controlla se process_text è disponibile
            has_process_text = hasattr(formatters_module, 'process_text')
            print(f"✓ Modulo formatters caricato, ha process_text: {'✓' if has_process_text else '✗'}")
            
            # Tenta di convertire la tabella
            try:
                result = formatters_module.process_table_html(test_table)
                print(f"✓ Conversione riuscita: {result[:100]}...")
            except Exception as e:
                print(f"✗ Errore nella conversione: {str(e)}")
                
                # Se manca process_text, proviamo a creare una funzione fittizia
                if not has_process_text and "process_text" in str(e):
                    print("Tentativo con una implementazione fittizia di process_text:")
                    
                    def process_text(text):
                        return text
                    
                    # Iniettiamo la funzione nel modulo
                    formatters_module.process_text = process_text
                    
                    # Riproviamo
                    try:
                        result = formatters_module.process_table_html(test_table)
                        print(f"✓ Conversione riuscita con process_text fittizio: {result[:100]}...")
                    except Exception as e2:
                        print(f"✗ Ancora errore: {str(e2)}")
    except Exception as e:
        print(f"✗ Errore nel caricamento del modulo: {str(e)}")
    
    # Test 5: Verifica il template HTML
    save_html_method = dump_method_source(formatters_path, 'save_analysis_to_html')
    
    # Cerca problemi nel template HTML
    if "<!DOCTYPE html>" in save_html_method:
        print("\n✓ Template HTML include DOCTYPE")
    else:
        print("\n✗ Template HTML non include DOCTYPE!")
    
    if "<html" in save_html_method and "<head>" in save_html_method:
        print("✓ Template HTML include tag html e head")
    else:
        print("✗ Template HTML non include tag html e/o head correttamente!")

if __name__ == "__main__":
    project_dir = '.'
    analyze_html_flow(project_dir)
    test_debug_process_table_html(project_dir)