# test_database_ui.py

import os
import json
import sqlite3
import gradio as gr
from datetime import datetime

class DatabaseDiagnostic:
    def __init__(self, db_path="crisp_projects.db"):
        self.db_path = db_path
        self.project_ids = []
        self.project_names = []
        self.log_messages = []
    
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.log_messages.append(log_entry)
        return "\n".join(self.log_messages)
    
    def verify_db_exists(self):
        exists = os.path.exists(self.db_path)
        self.log(f"Verifica database: {self.db_path} {'ESISTE' if exists else 'NON ESISTE'}")
        if exists:
            size = os.path.getsize(self.db_path)
            self.log(f"Dimensione database: {size} bytes")
        return exists
    
    def explore_db_structure(self):
        """Esplora la struttura del database e restituisce le informazioni sulle tabelle"""
        if not self.verify_db_exists():
            return "Database non trovato"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ottieni le tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            self.log(f"Tabelle trovate: {[t[0] for t in tables]}")
            
            # Analizza ogni tabella
            table_info = {}
            for table in tables:
                table_name = table[0]
                # Ottieni struttura
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Conta righe
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                # Campiona dati
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                sample = cursor.fetchone()
                
                table_info[table_name] = {
                    "columns": [col[1] for col in columns],
                    "row_count": count,
                    "sample": sample
                }
                
                self.log(f"Tabella '{table_name}': {count} righe, colonne: {[col[1] for col in columns]}")
                if sample:
                    self.log(f"Esempio riga: {sample}")
            
            conn.close()
            return table_info
            
        except Exception as e:
            self.log(f"Errore nell'esplorazione del DB: {str(e)}")
            return None
    
    def load_projects(self):
        """Carica i progetti dal database con debug dettagliato"""
        if not self.verify_db_exists():
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ottieni tutti i progetti
            cursor.execute("SELECT * FROM projects ORDER BY creation_date DESC")
            projects = cursor.fetchall()
            
            self.log(f"Progetti trovati: {len(projects)}")
            
            # Memorizza gli ID per riferimento
            self.project_ids = []
            self.project_names = []
            
            # Formatta i risultati per il debug
            formatted_projects = []
            for proj in projects[:5]:  # Limita a 5 per leggibilità
                proj_id = proj[0]
                self.project_ids.append(proj_id)
                
                # Ottieni dettagli progetto
                cursor.execute("""
                    SELECT variable_name, variable_value 
                    FROM project_variables 
                    WHERE project_id = ? AND variable_name = 'KEYWORD'
                """, (proj_id,))
                
                keyword_result = cursor.fetchone()
                keyword = keyword_result[1] if keyword_result else "N/A"
                
                # Formatta nome
                proj_name = f"{proj[1]} - {keyword} ({proj[2]})"
                self.project_names.append(proj_name)
                
                formatted_projects.append({
                    "id": proj_id,
                    "name": proj[1],
                    "creation_date": proj[2],
                    "keyword": keyword
                })
                
                self.log(f"Progetto {proj_id}: {proj_name}")
            
            conn.close()
            
            # Mostra sia gli ID che i nomi completi
            self.log("=== Struttura dati per debug ===")
            self.log(f"project_ids: {self.project_ids}")
            self.log(f"project_names: {self.project_names}")
            
            # Debug su come i dati saranno utilizzati nella UI
            self.log("=== Test di formattazione per UI ===")
            # 1. Lista di stringhe semplici
            self.log(f"Format 1 (stringhe): {self.project_names}")
            # 2. Lista di tuple (index, value)
            indexed = [(i, name) for i, name in enumerate(self.project_names)]
            self.log(f"Format 2 (tuple index): {indexed}")
            # 3. Lista di tuple (id, value)
            id_based = [(id, name) for id, name in zip(self.project_ids, self.project_names)]
            self.log(f"Format 3 (tuple id): {id_based}")
            
            return formatted_projects
            
        except Exception as e:
            self.log(f"Errore nel caricamento progetti: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return []
    
    def test_ui_components(self):
        """Testa diverse configurazioni di componenti UI con i dati dei progetti"""
        self.load_projects()
        
        def on_dropdown_change(value):
            self.log(f"Dropdown value changed: {value}")
            self.log(f"Type: {type(value)}")
            return value
        
        def on_radio_change(value):
            self.log(f"Radio value changed: {value}")
            self.log(f"Type: {type(value)}")
            return value
        
        with gr.Blocks() as demo:
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## Test di Componenti UI per Selezione Progetti")
                    log_output = gr.Textbox(value="", label="Log di diagnostica", lines=20)
                
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Test 1: Dropdown con type='value'")
                    dropdown1 = gr.Dropdown(
                        choices=self.project_names,
                        label="Progetti (type='value')",
                        value=self.project_names[0] if self.project_names else None,
                        type="value"
                    )
                    
                with gr.Column():
                    gr.Markdown("### Test 2: Dropdown con type='index'")
                    dropdown2 = gr.Dropdown(
                        choices=[(i, name) for i, name in enumerate(self.project_names)],
                        label="Progetti (type='index')",
                        value=0 if self.project_names else None,
                        type="index"
                    )
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Test 3: Radio Buttons")
                    radio = gr.Radio(
                        choices=self.project_names,
                        label="Progetti (Radio)"
                    )
                
                with gr.Column():
                    gr.Markdown("### Test 4: Dropdown con ID come value")
                    dropdown3 = gr.Dropdown(
                        choices=[(str(id), name) for id, name in zip(self.project_ids, self.project_names)],
                        label="Progetti (ID come value)",
                        type="value"
                    )
            
            # Eventi
            dropdown1.change(on_dropdown_change, inputs=dropdown1, outputs=log_output)
            dropdown2.change(on_dropdown_change, inputs=dropdown2, outputs=log_output)
            radio.change(on_radio_change, inputs=radio, outputs=log_output)
            dropdown3.change(on_dropdown_change, inputs=dropdown3, outputs=log_output)
            
        return demo

# Esegui i test
if __name__ == "__main__":
    diagnostic = DatabaseDiagnostic()
    diagnostic.verify_db_exists()
    diagnostic.explore_db_structure()
    diagnostic.load_projects()
    
    # Test dell'interfaccia UI
    test_ui = diagnostic.test_ui_components()
    test_ui.launch()