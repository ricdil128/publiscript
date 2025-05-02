#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
dependency_mapper.py - Strumento per mappare le duplicazioni e dipendenze nel codice
"""

import os
import re
import ast
import inspect
from difflib import SequenceMatcher
import traceback
from collections import defaultdict

class DuplicateCodeMapper:
    """Analizza il codice per trovare duplicazioni e mappare le dipendenze"""
    
    def __init__(self, project_root="."):
        self.project_root = os.path.abspath(project_root)
        self.python_files = []
        self.function_definitions = {}  # {nome_funzione: [percorso_file, linea_inizio, linea_fine]}
        self.method_calls = {}  # {nome_funzione: [lista_di_chiamate]}
        self.potential_duplicates = []  # [(funzione1, funzione2, somiglianza)]
        self.import_map = {}  # {file: [moduli_importati]}
        
    def find_python_files(self):
        """Trova tutti i file Python nel progetto"""
        print(f"Cercando file Python in {self.project_root}...")
        
        if not os.path.exists(self.project_root):
            print(f"ERRORE: Il percorso '{self.project_root}' non esiste!")
            return []
            
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    self.python_files.append(full_path)
        
        if len(self.python_files) > 0:
            print(f"Trovati {len(self.python_files)} file Python")
            for f in self.python_files[:5]:  # Mostra solo i primi 5 file
                print(f"  - {f}")
            if len(self.python_files) > 5:
                print(f"  - e altri {len(self.python_files) - 5} file...")
        else:
            print("Nessun file Python trovato!")
            
        return self.python_files
    
    def analyze_file(self, file_path):
        """Analizza un singolo file Python"""
        try:
            print(f"Analisi di {file_path}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            # Analizza l'AST per estrarre le funzioni e i metodi
            tree = ast.parse(file_content)
            tree = patch_ast(tree)  # Aggiungi riferimenti ai nodi genitori
            
            self._extract_functions(tree, file_path)
            self._extract_imports(tree, file_path)
            self._extract_method_calls(tree, file_path)
            return True
        except Exception as e:
            print(f"Errore durante l'analisi di {file_path}: {str(e)}")
            traceback.print_exc()
            return False
    
    def _extract_functions(self, tree, file_path):
        """Estrae tutte le definizioni di funzioni e metodi dal file"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                start_line = node.lineno
                end_line = self._find_function_end(node)
                
                # Per metodi di classe, aggiungi il nome della classe
                parent_class = self._get_parent_class(node)
                if parent_class:
                    full_name = f"{parent_class}.{func_name}"
                else:
                    full_name = func_name
                
                # Estrai il corpo della funzione per confronto
                func_body = self._extract_function_body(node, file_path)
                
                self.function_definitions[full_name] = {
                    'file': file_path,
                    'start': start_line,
                    'end': end_line,
                    'body': func_body
                }
    
    def _extract_function_body(self, node, file_path):
        """Estrae il corpo della funzione dal file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = node.lineno
            end_line = self._find_function_end(node)
            
            return ''.join(lines[start_line-1:end_line])
        except Exception:
            return ""
    
    def _find_function_end(self, node):
        """Trova la linea di fine di una funzione"""
        # Trova l'ultimo nodo all'interno della funzione
        max_line = node.lineno
        for child in ast.walk(node):
            if hasattr(child, 'lineno'):
                max_line = max(max_line, child.lineno)
        return max_line + 1  # Aggiungi 1 per includere l'ultima riga
    
    def _get_parent_class(self, node):
        """Ottiene il nome della classe genitore di un metodo"""
        parent = getattr(node, 'parent', None)
        if parent and isinstance(parent, ast.ClassDef):
            return parent.name
        return None
    
    def _extract_imports(self, tree, file_path):
        """Estrae tutti gli import dal file"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base = node.module + "."
                    for name in node.names:
                        imports.append(base + name.name)
        
        self.import_map[file_path] = imports
    
    def _extract_method_calls(self, tree, file_path):
        """Estrae tutte le chiamate a metodi nel file"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Funzioni semplici
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    self._add_method_call(func_name, file_path, node.lineno)
                
                # Metodi di classe o oggetto (es. self.method())
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    obj_name = node.func.value.id
                    method_name = node.func.attr
                    
                    # Se è un metodo self, cerca di determinare la classe
                    if obj_name == "self":
                        class_name = self._find_containing_class(node)
                        if class_name:
                            full_name = f"{class_name}.{method_name}"
                            self._add_method_call(full_name, file_path, node.lineno)
                    
                    # Altrimenti tratta come chiamata a oggetto generica
                    full_name = f"{obj_name}.{method_name}"
                    self._add_method_call(full_name, file_path, node.lineno)
    
    def _add_method_call(self, method_name, file_path, line_no):
        """Aggiunge una chiamata a metodo nel registro"""
        if method_name not in self.method_calls:
            self.method_calls[method_name] = []
        
        self.method_calls[method_name].append({
            'file': file_path,
            'line': line_no
        })
    
    def _find_containing_class(self, node):
        """Trova la classe che contiene il nodo corrente"""
        parent = getattr(node, 'parent', None)
        while parent:
            if isinstance(parent, ast.ClassDef):
                return parent.name
            parent = getattr(parent, 'parent', None)
        return None
    
    def analyze_project(self):
        """Analizza l'intero progetto"""
        if not self.python_files:
            self.find_python_files()
            
        if not self.python_files:
            print("Nessun file Python trovato! Verifica il percorso del progetto.")
            return {
                'files': 0,
                'functions': 0,
                'method_calls': 0,
                'duplicates': 0
            }
        
        for file_path in self.python_files:
            self.analyze_file(file_path)
        
        # Trova le potenziali duplicazioni
        self._find_duplicate_functions()
        
        print(f"Analisi completata: {len(self.function_definitions)} funzioni, {len(self.potential_duplicates)} duplicazioni potenziali")
        
        return {
            'files': len(self.python_files),
            'functions': len(self.function_definitions),
            'method_calls': sum(len(calls) for calls in self.method_calls.values()),
            'duplicates': len(self.potential_duplicates)
        }
    
    def _find_duplicate_functions(self):
        """Trova funzioni potenzialmente duplicate"""
        print("Ricerca duplicazioni...")
        # Confronta tutte le funzioni tra loro
        funcs = list(self.function_definitions.items())
        count = 0
        self.potential_duplicates = []  # Reset per sicurezza
        
        for i in range(len(funcs)):
            for j in range(i+1, len(funcs)):
                name1, data1 = funcs[i]
                name2, data2 = funcs[j]
                
                # Non confrontare funzioni con lo stesso nome (potrebbero essere override)
                if name1.split('.')[-1] == name2.split('.')[-1] and name1 != name2:
                    continue
                
                # Confronta il corpo delle funzioni
                body1 = data1['body']
                body2 = data2['body']
                
                # Calcola la somiglianza escludendo i commenti
                similarity = self._calculate_similarity(body1, body2)
                
                # Se la somiglianza è alta, è probabile una duplicazione
                if similarity > 0.7:  # Soglia configurabile
                    self.potential_duplicates.append((name1, name2, similarity))
                    count += 1
                    if count % 10 == 0:
                        print(f"  - Trovate {count} duplicazioni...")
                        
        print(f"Trovate {len(self.potential_duplicates)} duplicazioni potenziali")
    
    def _calculate_similarity(self, text1, text2):
        """Calcola la somiglianza tra due testi escludendo commenti e docstring"""
        # Rimuovi i commenti
        def remove_comments(text):
            lines = []
            for line in text.split('\n'):
                if '#' in line:
                    line = line.split('#')[0]
                line = line.strip()
                if line:
                    lines.append(line)
            return '\n'.join(lines)
        
        clean1 = remove_comments(text1)
        clean2 = remove_comments(text2)
        
        # Calcola la somiglianza
        matcher = SequenceMatcher(None, clean1, clean2)
        return matcher.ratio()
    
    def generate_report(self, output_file="duplicates_report.html"):
        """Genera un report HTML delle duplicazioni e dipendenze"""
        print(f"Generazione report in {output_file}...")
        
        # Creiamo l'HTML manualmente senza usare .format()
        html_parts = []
        
        # Header
        html_parts.append('''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analisi Duplicazioni Codice</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            line-height: 1.6; 
        }
        h1, h2, h3 { 
            color: #333; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        .card { 
            background: #fff; 
            border-radius: 5px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px; 
            padding: 20px; 
        }
        .metric { 
            display: inline-block; 
            margin-right: 20px; 
            padding: 10px;
            background: #f5f5f5; 
            border-radius: 5px; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
            margin: 20px 0; 
        }
        table, th, td { 
            border: 1px solid #ddd; 
        }
        th, td { 
            padding: 12px; 
            text-align: left; 
        }
        th { 
            background-color: #f2f2f2; 
        }
        tr:nth-child(even) { 
            background-color: #f9f9f9; 
        }
        .similarity-high { 
            background-color: #ffdddd; 
        }
        .similarity-medium { 
            background-color: #ffffcc; 
        }
        .function-code { 
            font-family: monospace; 
            white-space: pre-wrap; 
            font-size: 12px;
            max-height: 300px; 
            overflow-y: auto; 
            background: #f5f5f5;
            padding: 10px; 
            border: 1px solid #ddd; 
            margin-top: 10px; 
        }
        .badge { 
            display: inline-block; 
            padding: 3px 8px; 
            border-radius: 3px;
            font-size: 12px; 
            font-weight: bold; 
            color: white; 
        }
        .badge-high { 
            background-color: #d9534f; 
        }
        .badge-medium { 
            background-color: #f0ad4e; 
        }
        .badge-low { 
            background-color: #5bc0de; 
        }
        .tab { 
            overflow: hidden; 
            border: 1px solid #ccc; 
            background-color: #f1f1f1; 
        }
        .tab button { 
            background-color: inherit; 
            float: left; 
            border: none; 
            outline: none;
            cursor: pointer; 
            padding: 14px 16px; 
            transition: 0.3s; 
        }
        .tab button:hover { 
            background-color: #ddd; 
        }
        .tab button.active { 
            background-color: #ccc; 
        }
        .tabcontent { 
            display: none; 
            padding: 6px 12px; 
            border: 1px solid #ccc;
            border-top: none; 
        }
        #duplicates { 
            display: block; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Analisi Duplicazioni Codice</h1>
        <div class="card">
            <h2>Metriche Progetto</h2>''')
        
        # Metriche
        metrics = {
            'files': len(self.python_files),
            'functions': len(self.function_definitions),
            'method_calls': sum(len(calls) for calls in self.method_calls.values()),
            'duplicates': len(self.potential_duplicates)
        }
        
        html_parts.append(f'''
            <div class="metric"><strong>File Python:</strong> {metrics['files']}</div>
            <div class="metric"><strong>Funzioni/Metodi:</strong> {metrics['functions']}</div>
            <div class="metric"><strong>Chiamate a Metodi:</strong> {metrics['method_calls']}</div>
            <div class="metric"><strong>Potenziali Duplicazioni:</strong> {metrics['duplicates']}</div>
        </div>
        
        <div class="tab">
            <button class="tablinks active" onclick="openTab(event, 'duplicates')">Duplicazioni</button>
            <button class="tablinks" onclick="openTab(event, 'dependencies')">Dipendenze</button>
            <button class="tablinks" onclick="openTab(event, 'functions')">Funzioni</button>
        </div>
        
        <div id="duplicates" class="tabcontent">
            <div class="card">
                <h2>Potenziali Duplicazioni</h2>
                <table>
                    <tr>
                        <th>Funzione 1</th>
                        <th>Funzione 2</th>
                        <th>Somiglianza</th>
                        <th>Dettagli</th>
                    </tr>''')
        
        # Duplicati
        for i, (func1, func2, similarity) in enumerate(sorted(self.potential_duplicates, key=lambda x: x[2], reverse=True)):
            func1_data = self.function_definitions[func1]
            func2_data = self.function_definitions[func2]
            
            # Determina la classe per la somiglianza
            sim_class = "similarity-high" if similarity > 0.9 else "similarity-medium"
            badge_class = "badge-high" if similarity > 0.9 else "badge-medium"
            
            # Sanifica il corpo delle funzioni per HTML
            func1_body = func1_data['body'].replace('<', '&lt;').replace('>', '&gt;')
            func2_body = func2_data['body'].replace('<', '&lt;').replace('>', '&gt;')
            
            html_parts.append(f'''
                    <tr class="{sim_class}">
                        <td>
                            <strong>{func1}</strong><br>
                            <small>{func1_data['file']} (linee {func1_data['start']}-{func1_data['end']})</small>
                        </td>
                        <td>
                            <strong>{func2}</strong><br>
                            <small>{func2_data['file']} (linee {func2_data['start']}-{func2_data['end']})</small>
                        </td>
                        <td>
                            <span class="badge {badge_class}">{similarity:.2f}</span>
                        </td>
                        <td>
                            <button onclick="toggleCode('code-{i}')">Mostra/Nascondi Codice</button>
                            <div id="code-{i}" class="function-code" style="display: none;">
                                <h4>Funzione 1:</h4>
                                {func1_body}
                                
                                <h4>Funzione 2:</h4>
                                {func2_body}
                            </div>
                        </td>
                    </tr>''')
        
        html_parts.append('''
                </table>
            </div>
        </div>
        
        <div id="dependencies" class="tabcontent">
            <div class="card">
                <h2>Mappa Dipendenze</h2>
                <table>
                    <tr>
                        <th>Funzione/Metodo</th>
                        <th>Chiamate</th>
                    </tr>''')
        
        # Dipendenze
        for method, calls in sorted(self.method_calls.items(), key=lambda x: len(x[1]), reverse=True):
            if method in self.function_definitions:
                func_info = self.function_definitions[method]
                file_path = func_info['file']
                start_line = func_info['start']
            else:
                file_path = "Non trovato nel progetto"
                start_line = "N/A"
            
            calls_list = "<ul>"
            for call in calls[:10]:  # Limita a 10 chiamate per brevità
                calls_list += f"<li>{call['file']}:{call['line']}</li>"
            if len(calls) > 10:
                calls_list += f"<li>... e altre {len(calls)-10} chiamate</li>"
            calls_list += "</ul>"
            
            html_parts.append(f'''
                    <tr>
                        <td>
                            <strong>{method}</strong><br>
                            <small>{file_path}:{start_line}</small>
                        </td>
                        <td>
                            {calls_list}
                        </td>
                    </tr>''')
        
        html_parts.append('''
                </table>
            </div>
        </div>
        
        <div id="functions" class="tabcontent">
            <div class="card">
                <h2>Elenco Funzioni</h2>
                <table>
                    <tr>
                        <th>Nome</th>
                        <th>File</th>
                        <th>Linee</th>
                    </tr>''')
        
        # Funzioni
        for func_name, data in sorted(self.function_definitions.items()):
            html_parts.append(f'''
                    <tr>
                        <td><strong>{func_name}</strong></td>
                        <td>{os.path.basename(data['file'])}</td>
                        <td>{data['start']}-{data['end']}</td>
                    </tr>''')
        
        # Script alla fine
        html_parts.append('''
                </table>
            </div>
        </div>
    </div>
    
    <script>
    function openTab(evt, tabName) {
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
    }
    
    function toggleCode(id) {
        var x = document.getElementById(id);
        if (x.style.display === "none") {
            x.style.display = "block";
        } else {
            x.style.display = "none";
        }
    }
    </script>
</body>
</html>''')
        
        # Unisci tutte le parti
        complete_html = ''.join(html_parts)
        
        # Scrivi il report su file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(complete_html)
        
        print(f"Report generato: {output_file}")
        return output_file


def patch_ast(tree):
    """Aggiunge riferimenti ai nodi genitori nell'AST"""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child.parent = parent
    return tree


def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analizza le duplicazioni di codice in un progetto Python')
    parser.add_argument('--path', default='.', help='Path to project root directory')
    parser.add_argument('--output', default='duplicates_report.html', help='Output report file')
    args = parser.parse_args()
    
    print(f"Analisi del progetto in: {args.path}")
    mapper = DuplicateCodeMapper(args.path)
    mapper.find_python_files()
    
    # Controlla se ci sono file Python prima di procedere
    if not mapper.python_files:
        print("Nessun file Python trovato! Verifica il percorso del progetto.")
        return
    
    # Esegui l'analisi
    mapper.analyze_project()
    
    # Genera il report
    report_path = mapper.generate_report(args.output)
    print(f"Analisi completata! Report disponibile in: {report_path}")


if __name__ == "__main__":
    main()