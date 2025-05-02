"""
Gestore del database per PubliScript.
Gestisce tutte le operazioni relative al database per l'applicazione.
"""

import re
import sqlite3
import time
import logging
import os
import json
import traceback
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, project_db_path="crisp_projects.db", log_callback=None):
        """
        Inizializza il gestore del database.
        
        Args:
            project_db_path: Percorso del file di database
            log_callback: Funzione di callback per il logging (opzionale)
        """
        self.project_db_path = project_db_path
        self.log_callback = log_callback
        
        # Proprietà per mantenere gli indici e i dati dei progetti
        self.project_ids_by_index = []
        self.projects_data = {}
        self.projects_details = {}

    def add_log(self, message):
        """Utilizza il callback di log se disponibile"""
        if self.log_callback:
            return self.log_callback(message)
        else:
            print(f"DB_LOG: {message}")
            return message

    def safe_db_operation(func):
        """Decoratore per gestire in modo sicuro le operazioni sul database"""
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except sqlite3.Error as sql_e:
                error_msg = f"Errore SQLite in {func.__name__}: {str(sql_e)}"
                self.add_log(f"❌ {error_msg}")
                return f"❌ {error_msg}"
            except Exception as e:
                error_msg = f"Errore in {func.__name__}: {str(e)}"
                self.add_log(f"❌ {error_msg}")
                traceback.print_exc()
                self.add_log(traceback.format_exc())
                return f"❌ {error_msg}"
        return wrapper

    def recupera_ultimo_progetto(self):
        """Recupera l'ID dell'ultimo progetto creato nel database."""
        try:
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM projects ORDER BY creation_date DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()
        
            if result:
                self.add_log(f"Recuperato ultimo progetto: {result[0]} - {result[1]}")
                return result[0]  # Return project ID
            self.add_log("Nessun progetto trovato nel database")
            return None
        except Exception as e:
            self.add_log(f"Errore nel recupero dell'ultimo progetto: {str(e)}")
            return None

    @safe_db_operation
    def ripristina_analisi_da_database(self, selected_index, start_from_phase=None, driver=None, crisp=None, chat_manager=None):
        """
        Ripristina un'analisi dal database e continua da una fase specifica.
    
        Args:
            selected_index: Indice del progetto selezionato nel dropdown
            start_from_phase: Fase da cui riprendere (es. "CS-2"), se None usa l'ultima fase completata
            driver: Riferimento al driver browser
            crisp: Riferimento all'oggetto CRISP
            chat_manager: Riferimento al gestore chat
    
        Returns:
            str: Log dell'operazione
        """
        try:
            self.add_log(f"Tentativo di ripristino analisi dall'indice: {selected_index}")
        
            # Determina l'ID del progetto dall'indice selezionato
            project_id = None
        
            # Se non abbiamo la lista degli ID per indice, ricaricare i progetti
            if not self.project_ids_by_index:
                self.add_log("⚠️ Lista ID non disponibile, ricaricamento in corso...")
                self.load_projects_list()
            
            # Verificare se l'indice è valido
            if isinstance(selected_index, (int, float)):
                index = int(selected_index)
                if 0 <= index < len(self.project_ids_by_index):
                    project_id = self.project_ids_by_index[index]
                    self.add_log(f"ID progetto dall'indice {index}: {project_id}")
                else:
                    self.add_log(f"⚠️ Indice fuori range: {index}")
        
            # Se non abbiamo un ID valido, fallback al primo progetto
            if not project_id:
                if self.project_ids_by_index:
                    project_id = self.project_ids_by_index[0]
                    self.add_log(f"📌 Usando primo progetto disponibile: {project_id}")
                else:
                    # Recupera il primo progetto dal database
                    conn = sqlite3.connect(self.project_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM projects LIMIT 1")
                    result = cursor.fetchone()
                    conn.close()
                
                    if result:
                        project_id = result[0]
                        self.add_log(f"📌 Recuperato primo progetto dal DB: {project_id}")
                    else:
                        self.add_log("❌ Nessun progetto trovato nel database")
                        return "❌ Nessun progetto trovato nel database"
        
            self.add_log(f"Tentativo di ripristino analisi dal database (ID: {project_id})")
        
            # 1. Recupera i dati del progetto
            try:
                if crisp:
                    project_data = crisp.get_project_data(project_id)
                    if not project_data:
                        return self.add_log("❌ Impossibile recuperare i dati del progetto")
                else:
                    self.add_log("⚠️ Oggetto CRISP non disponibile")
                    return "⚠️ Oggetto CRISP non disponibile"
            except Exception as project_error:
                self.add_log(f"❌ Errore nel recupero dei dati del progetto: {str(project_error)}")
                return f"❌ Errore nel recupero dei dati del progetto: {str(project_error)}"
        
            self.add_log(f"Dati progetto recuperati: {project_data.get('PROJECT_NAME', 'N/A')}")
        
            # 2. Trova l'ultima fase completata se non specificata
            if not start_from_phase:
                if crisp:
                    completed_phases = crisp.get_completed_phases(project_id)
                    if not completed_phases:
                        return self.add_log("❌ Nessuna fase completata trovata per questo progetto")
                
                    # Ordina le fasi per trovare l'ultima
                    phase_order = ["CM-1", "CM-2", "CS-1", "CS-2", "CS-3", "CP-1", "CP-2", "CPM-1", "CPM-2", "CPM-3", "CS-F"]
                    valid_phases = [p for p in completed_phases if p in phase_order]
                
                    if not valid_phases:
                        return self.add_log("❌ Nessuna fase CRISP valida trovata")
                
                    # Trova l'ultima fase completata
                    last_completed = max(valid_phases, key=lambda p: phase_order.index(p))
                
                    # Trova la fase successiva
                    try:
                        next_index = phase_order.index(last_completed) + 1
                        if next_index < len(phase_order):
                            start_from_phase = phase_order[next_index]
                            self.add_log(f"✅ Fase successiva identificata: {start_from_phase}")
                        else:
                            return self.add_log("✅ Tutte le fasi sono state completate")
                    except ValueError:
                        return self.add_log("❌ Errore nell'identificare la fase successiva")
                else:
                    return self.add_log("⚠️ Impossibile determinare la fase successiva: CRISP non disponibile")
        
            # 3. Restituisci i dati necessari per ripristinare l'analisi
            return {
                "project_id": project_id,
                "project_data": project_data,
                "current_phase": start_from_phase
            }
    
        except Exception as e:
            error_msg = f"❌ Errore nel ripristino dell'analisi: {str(e)}"
            self.add_log(error_msg)
            print(f"ERRORE DETTAGLIATO: {traceback.format_exc()}")
            return f"❌ Errore nel ripristino dell'analisi: {str(e)}"

    def ripristina_ultima_analisi(self, crisp=None, driver=None, chat_manager=None):
        """Ripristina l'ultima analisi dal database."""
        try:
            # Recupera l'ultimo progetto
            project_id = self.recupera_ultimo_progetto()
            if not project_id:
                return self.add_log("Nessun progetto trovato da ripristinare")
    
            # Ripristina l'analisi
            return self.ripristina_analisi_da_database(None, None, driver, crisp, chat_manager, project_id=project_id)
        
        except Exception as e:
            self.add_log(f"Errore nel ripristino dell'analisi: {str(e)}")
            return f"Errore nel ripristino dell'analisi: {str(e)}"

    @safe_db_operation
    def load_projects_list(self):
        """Carica la lista dei progetti dal database adattato alla struttura effettiva"""
        self.add_log("🔄 Caricamento progetti dal database...")

        try:
            # Verifica che il database esista
            if not os.path.exists(self.project_db_path):
                self.add_log(f"⚠️ Database non trovato: {self.project_db_path}")
                return []
    
            self.add_log(f"📂 Database trovato: {self.project_db_path}")
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
    
            # Query base che utilizza la struttura effettiva del database
            cursor.execute("""
                SELECT p.id, p.name, p.creation_date, p.status
                FROM projects p
                ORDER BY p.creation_date DESC
            """)
    
            projects = cursor.fetchall()
    
            # Se ci sono progetti, cerca di ottenere le keyword
            project_keywords = {}
            if projects:
                for project in projects:
                    project_id = project[0]
                    # Usa la struttura effettiva con variable_name e variable_value
                    cursor.execute("""
                        SELECT variable_value 
                        FROM project_variables 
                        WHERE project_id = ? AND variable_name = 'KEYWORD'
                    """, (project_id,))
            
                    keyword_result = cursor.fetchone()
                    keyword = keyword_result[0] if keyword_result else "Keyword non specificata"
                    project_keywords[project_id] = keyword
            
            conn.close()
    
            if not projects:
                self.add_log("ℹ️ Nessun progetto trovato nel database")
                return []
    
            # Formatta i risultati
            formatted_projects = []
            display_choices = []  # Questo sarà un elenco di stringhe per il dropdown
            self.project_ids_by_index = []  # Questo sarà un elenco di ID progetti corrispondenti agli indici
    
            for proj in projects:
                try:
                    # Estrai le informazioni base
                    proj_id = proj[0]    # id
                    proj_name = proj[1]  # name
                    date_str = proj[2]   # creation_date
                    proj_status = proj[3]  # status
                    proj_keyword = project_keywords.get(proj_id, "")
            
                    # Formatta la data
                    try:
                        if date_str and isinstance(date_str, str):
                            if 'T' in date_str:  # Formato ISO
                                date_formatted = datetime.fromisoformat(date_str).strftime('%d/%m/%Y %H:%M')
                            else:
                                date_formatted = date_str
                        else:
                            date_formatted = str(date_str)
                    except Exception as date_error:
                        self.add_log(f"⚠️ Errore nella formattazione della data: {str(date_error)}")
                        date_formatted = str(date_str)
            
                    # Display informativo
                    display_name = f"{proj_name} - {proj_keyword} ({date_formatted})"
            
                    project_data = {
                        "id": proj_id,
                        "name": proj_name,
                        "date": date_formatted,
                        "status": proj_status,
                        "keyword": proj_keyword,
                        "display": display_name
                    }
            
                    formatted_projects.append(project_data)
                    display_choices.append(display_name)  # Solo il nome da visualizzare
                    self.project_ids_by_index.append(proj_id)  # Salva l'ID nella stessa posizione
            
                except Exception as item_error:
                    self.add_log(f"⚠️ Errore nella formattazione del progetto: {str(item_error)}")
                    traceback.print_exc()
                    self.add_log(traceback.format_exc())
                    continue
    
            # Salva progetti in dizionario per uso futuro
            self.projects_data = {p["display"]: p["id"] for p in formatted_projects}
            self.projects_details = {p["id"]: p for p in formatted_projects}
    
            self.add_log(f"✅ Caricati {len(formatted_projects)} progetti dal database")
    
            return display_choices  # Restituisci solo i nomi da visualizzare per il dropdown
    
        except Exception as e:
            self.add_log(f"❌ Errore generale nel caricamento progetti: {str(e)}")
            traceback.print_exc()
            error_details = traceback.format_exc()
            self.add_log(f"📄 Dettagli errore: {error_details}")
            print(f"Errore dettagliato: {error_details}")
            return []

    @safe_db_operation
    def check_existing_analysis(self, keyword):
        """
        Verifica se esiste già un'analisi per la keyword specificata.
    
        Args:
            keyword: Keyword da cercare
        
        Returns:
            tuple: (esiste, project_id, data_creazione) o (False, None, None)
        """
        try:
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Cerca progetti con questa keyword
            cursor.execute("""
                SELECT p.id, p.creation_date 
                FROM projects p
                JOIN project_variables v ON p.id = v.project_id
                WHERE v.name = 'KEYWORD' AND v.value = ?
                ORDER BY p.creation_date DESC
                LIMIT 1
            """, (keyword,))
        
            result = cursor.fetchone()
            conn.close()
        
            if result:
                project_id, creation_date = result
                date_formatted = datetime.fromisoformat(creation_date).strftime('%d/%m/%Y %H:%M')
                return True, project_id, date_formatted
        
            return False, None, None
        
        except Exception as e:
            self.add_log(f"Errore nella verifica di analisi esistenti: {str(e)}")
            return False, None, None    

    @safe_db_operation
    def load_project_details(self, selected_index):
        """Carica i dettagli di un progetto basandosi sull'indice selezionato"""
        self.add_log(f"🔍 Caricamento dettagli per indice: {selected_index}")
    
        try:
            # Verifica che l'indice sia valido
            if selected_index is None:
                self.add_log("⚠️ Nessun progetto selezionato")
                return "<div class='project-placeholder'>Seleziona un progetto dalla lista per visualizzarne i dettagli</div>"
        
            # Converti l'indice in ID progetto
            project_id = None
        
            # Se non abbiamo la lista degli ID per indice, ricaricare i progetti
            if not self.project_ids_by_index:
                self.add_log("⚠️ Lista ID non disponibile, ricaricamento in corso...")
                self.load_projects_list()
        
            # Verifica che l'indice sia un numero e sia all'interno del range valido
            if isinstance(selected_index, (int, float)):
                index = int(selected_index)
                if 0 <= index < len(self.project_ids_by_index):
                    project_id = self.project_ids_by_index[index]
                    self.add_log(f"ID progetto dall'indice {index}: {project_id}")
                else:
                    self.add_log(f"⚠️ Indice fuori range: {index}, max: {len(self.project_ids_by_index)-1 if self.project_ids_by_index else 'N/A'}")
            else:
                self.add_log(f"⚠️ Indice non valido: {selected_index} (tipo: {type(selected_index).__name__})")
        
            # Se non abbiamo un ID valido, fallback al primo progetto
            if not project_id:
                if self.project_ids_by_index:
                    project_id = self.project_ids_by_index[0]
                    self.add_log(f"📌 Usando primo progetto disponibile: {project_id}")
                else:
                    # Recupera il primo progetto dal database
                    conn = sqlite3.connect(self.project_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM projects LIMIT 1")
                    result = cursor.fetchone()
                    conn.close()
                
                    if result:
                        project_id = result[0]
                        self.add_log(f"📌 Recuperato primo progetto dal DB: {project_id}")
                    else:
                        self.add_log("❌ Nessun progetto trovato nel database")
                        return "<div class='error-message'>Nessun progetto trovato nel database.</div>"
        
            # Da qui in poi, continuiamo con la logica esistente
            self.add_log(f"📌 Caricamento dettagli progetto: {project_id}")
        
            # Recupero dati dal database
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Recupera dati progetto
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_base = cursor.fetchone()
        
            if not project_base:
                conn.close()
                self.add_log("❌ Progetto non trovato nel database")
                return "<div class='error-message'>Progetto non trovato nel database.</div>"
        
            # Recupera variabili progetto
            cursor.execute("SELECT variable_name, variable_value FROM project_variables WHERE project_id = ?", (project_id,))
            variables = cursor.fetchall()
        
            # Recupera risultati
            cursor.execute("SELECT step_id, result_text, timestamp FROM project_results WHERE project_id = ? ORDER BY timestamp", (project_id,))
            results = cursor.fetchall()
        
            conn.close()
        
            # Converti a dizionario
            project_data = {
                "id": project_base[0],
                "name": project_base[1],
                "creation_date": project_base[2],
                "status": project_base[3]
            }
        
            # Aggiungi variabili al dizionario
            for var_name, var_value in variables:
                project_data[var_name] = var_value
        
            # HTML per i dettagli
            html_details = f"""
            <div style="font-family: Arial, sans-serif; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                <h2 style="color: #2c3e50;">{project_data.get('name', 'Progetto')}</h2>
            
                <div style="display: flex; margin-bottom: 15px;">
                    <div style="flex: 1; background: #f7f7f7; padding: 10px; border-radius: 5px; margin-right: 10px;">
                        <h3 style="margin-top: 0; color: #3498db;">Informazioni Progetto</h3>
                        <p><strong>ID:</strong> {project_id}</p>
                        <p><strong>Data creazione:</strong> {project_data.get('creation_date', 'N/A')}</p>
                        <p><strong>Stato:</strong> {project_data.get('status', 'N/A')}</p>
                        <p><strong>Keyword:</strong> {project_data.get('KEYWORD', 'N/A')}</p>
                    </div>
            
                    <div style="flex: 1; background: #f7f7f7; padding: 10px; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #e74c3c;">Dettagli Libro</h3>
                        <p><strong>Titolo:</strong> {project_data.get('TITOLO_LIBRO', 'N/A')}</p>
                        <p><strong>Stile voce:</strong> {project_data.get('VOICE_STYLE', 'N/A')}</p>
                    </div>
                </div>
            
                <h3 style="color: #9b59b6;">Contenuto</h3>
                <div style="background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 15px;">
                    <pre>{project_data.get('CONTENT_PILLARS', 'Nessun indice disponibile')}</pre>
                </div>
            
                <h3 style="color: #f39c12;">Risultati Salvati</h3>
                <div style="max-height: 200px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #3498db; color: white;">
                            <th style="padding: 8px; text-align: left;">Step</th>
                            <th style="padding: 8px; text-align: left;">Timestamp</th>
                            <th style="padding: 8px; text-align: left;">Anteprima</th>
                        </tr>
            """
        
            # Aggiungi risultati alla tabella
            result_rows = ""
            if results:
                for step_id, result_text, timestamp in results:
                    preview = result_text[:50] + "..." if result_text and len(result_text) > 50 else "Nessun testo"
                    result_rows += f"""
                    <tr style="background-color: #f5f5f5;">
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{step_id}</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{timestamp}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{preview}</td>
                    </tr>
                    """
            else:
                result_rows = """
                <tr>
                    <td colspan="3" style="text-align: center; padding: 10px;">Nessun risultato salvato</td>
                </tr>
                """
        
            html_details += result_rows
        
            html_details += """
                    </table>
                </div>
            
                <div style="margin-top: 20px;">
                    <p style="color: #7f8c8d;"><em>Per riprendere l'analisi da dove è stata interrotta, usa il pulsante "Ripristina Analisi"</em></p>
                </div>
            </div>
            """
        
            self.add_log("✅ Dettagli progetto caricati con successo")
            return html_details
        
        except Exception as e:
            error_msg = f"❌ Errore nel caricamento dei dettagli: {str(e)}"
            self.add_log(error_msg)
            traceback.print_exc()
            error_details = traceback.format_exc()
            self.add_log(error_details)
            return f"""
            <div style='color: red; padding: 20px; background-color: #ffebee; border-radius: 5px; border: 1px solid #ffcccc;'>
                <h3>Errore nel caricamento dei dettagli</h3>
                <p>{str(e)}</p>
                <pre style='background-color: #f8f8f8; padding: 10px; overflow: auto; max-height: 200px; font-size: 12px;'>{error_details}</pre>
            </div>
            """

    @safe_db_operation
    def diagnose_and_fix_database(self):
        """Diagnosi e riparazione del database"""
        self.add_log("🔍 Avvio diagnosi database...")
    
        db_path = self.project_db_path
        self.add_log(f"🗂️ Posizione database: {db_path}")
    
        # Verifica se il file esiste
        if not os.path.exists(db_path):
            self.add_log("⚠️ Database non trovato! Creazione nuovo database...")
            self.initialize_database()
            return "Database creato con successo!"
    
        # Il database esiste, verifica la struttura
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
        
            # Controlla tabelle esistenti
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            self.add_log(f"📋 Tabelle trovate: {', '.join(tables) if tables else 'nessuna'}")
        
            # Verifica ed eventualmente crea le tabelle mancanti
            required_tables = ["projects", "project_variables", "project_results", "incremental_responses"]
            missing_tables = [table for table in required_tables if table not in tables]
        
            if missing_tables:
                self.add_log(f"⚠️ Tabelle mancanti: {', '.join(missing_tables)}")
                self.initialize_database(existing_tables=tables)
            else:
                self.add_log("✅ Tutte le tabelle richieste esistono")
            
                # Conta i progetti
                cursor.execute("SELECT COUNT(*) FROM projects")
                count = cursor.fetchone()[0]
                self.add_log(f"📊 Progetti nel database: {count}")
        
            conn.close()
            return "Diagnosi database completata"
        
        except Exception as e:
            self.add_log(f"❌ Errore durante la diagnosi: {str(e)}")
            traceback.print_exc()
            self.add_log(traceback.format_exc())
            return f"Errore: {str(e)}"
        
    def initialize_database(self, existing_tables=None):
        """Inizializza il database con la struttura corretta"""
        try:
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Definizione tabelle
            tables = {
                "projects": """
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        creation_date TEXT,
                        last_updated TEXT
                    )
                """,
                "project_variables": """
                    CREATE TABLE IF NOT EXISTS project_variables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        name TEXT,
                        value TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """,
                "project_results": """
                    CREATE TABLE IF NOT EXISTS project_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        prompt_id TEXT,
                        created_at TEXT,
                        data TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """,
                "incremental_responses": """
                    CREATE TABLE IF NOT EXISTS incremental_responses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER,
                        section TEXT,
                        data TEXT,
                        created_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES projects (id)
                    )
                """
            }
        
            # Crea solo le tabelle mancanti
            for table_name, create_sql in tables.items():
                if existing_tables is None or table_name not in existing_tables:
                    self.add_log(f"🔧 Creazione tabella: {table_name}")
                    cursor.execute(create_sql)
        
            conn.commit()
            conn.close()
            self.add_log("✅ Database inizializzato correttamente")
        
        except Exception as e:
            self.add_log(f"❌ Errore durante l'inizializzazione del database: {str(e)}")

    @safe_db_operation
    def export_project(self, selected_index):
        """Esporta un progetto in formato JSON"""
        try:
            self.add_log(f"Richiesta esportazione dal progetto con indice: {selected_index}")
        
            # Determinazione dell'ID progetto dall'indice
            project_id = None
        
            # Se non abbiamo la lista degli ID per indice, ricaricare i progetti
            if not self.project_ids_by_index:
                self.add_log("⚠️ Lista ID non disponibile, ricaricamento in corso...")
                self.load_projects_list()
            
            # Verificare se l'indice è valido
            if isinstance(selected_index, (int, float)):
                index = int(selected_index)
                if 0 <= index < len(self.project_ids_by_index):
                    project_id = self.project_ids_by_index[index]
                    self.add_log(f"ID progetto dall'indice {index}: {project_id}")
                else:
                    self.add_log(f"⚠️ Indice fuori range: {index}")
        
            # Se non abbiamo un ID valido, fallback al primo progetto
            if not project_id:
                if self.project_ids_by_index:
                    project_id = self.project_ids_by_index[0]
                    self.add_log(f"📌 Usando primo progetto disponibile: {project_id}")
                else:
                    # Recupera il primo progetto dal database
                    conn = sqlite3.connect(self.project_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM projects LIMIT 1")
                    result = cursor.fetchone()
                    conn.close()
                
                    if result:
                        project_id = result[0]
                        self.add_log(f"📌 Recuperato primo progetto dal DB: {project_id}")
                    else:
                        self.add_log("❌ Nessun progetto trovato nel database")
                        return "Errore: Nessun progetto trovato nel database"
        
            # Recupera i dati del progetto
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Recupera i dati base del progetto
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project_base = cursor.fetchone()
        
            if not project_base:
                conn.close()
                self.add_log(f"❌ Progetto {project_id} non trovato")
                return "Errore: Progetto non trovato nel database"
        
            # Recupera tutte le variabili
            cursor.execute("""
                SELECT variable_name, variable_value 
                FROM project_variables 
                WHERE project_id = ?
            """, (project_id,))
            variables = cursor.fetchall()
        
            # Recupera tutti i risultati
            cursor.execute("""
                SELECT step_id, result_text, timestamp 
                FROM project_results 
                WHERE project_id = ?
                ORDER BY timestamp
            """, (project_id,))
            results = cursor.fetchall()
        
            conn.close()
        
            # Crea il dizionario di esportazione
            export_data = {
                "id": project_id,
                "name": project_base[1],
                "creation_date": project_base[2],
                "status": project_base[3],
                "variables": {name: value for name, value in variables},
                "results": [{"step_id": step, "text": text, "timestamp": ts} for step, text, ts in results]
            }
        
            # Converti in JSON
            import json
            export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
        
            # Crea un file temporaneo
            import tempfile
            import os
            temp_dir = tempfile.gettempdir()
            export_file = os.path.join(temp_dir, f"publiscript_export_{project_id}.json")
        
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(export_json)
        
            self.add_log(f"✅ Progetto esportato in: {export_file}")
        
            # Messaggio di successo
            success_message = f"""
            <div style="background-color: #e7f5ea; padding: 15px; border-radius: 5px; border: 1px solid #4caf50;">
                <h3>✅ Progetto Esportato con Successo</h3>
                <p><strong>ID:</strong> {project_id}</p>
                <p><strong>Nome:</strong> {project_base[1]}</p>
                <p><strong>File:</strong> {export_file}</p>
                <p>Il file è stato salvato sul tuo computer. Puoi aprirlo con qualsiasi editor di testo.</p>
            </div>
            """
        
            return success_message
        
        except Exception as e:
            error_msg = f"❌ Errore nell'esportazione: {str(e)}"
            self.add_log(error_msg)
            traceback.print_exc()
            error_details = traceback.format_exc()
            self.add_log(error_details)
            return f"""
            <div style='color: red; padding: 20px; background-color: #ffebee; border-radius: 5px; border: 1px solid #ffcccc;'>
                <h3>Errore nell'Esportazione</h3>
                <p>{str(e)}</p>
                <pre style='background-color: #f8f8f8; padding: 10px; overflow: auto; max-height: 200px; font-size: 12px;'>{error_details}</pre>
            </div>
            """
    
    def update_project_count(self):
        """Aggiorna il contatore dei progetti"""
        try:
            # Conta i progetti nel database
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM projects")
            count = cursor.fetchone()[0]
            conn.close()
        
            if count == 0:
                return """
                <div style="background-color: #fff3e0; padding: 5px 10px; border-radius: 5px; display: inline-block;">
                    <strong>0</strong> progetti nel database
                </div>
                """
            else:
                return f"""
                <div style="background-color: #e8f5e9; padding: 5px 10px; border-radius: 5px; display: inline-block;">
                    <strong>{count}</strong> progetti nel database
                </div>
                """
        except Exception as e:
            self.add_log(f"Errore nel conteggio progetti: {str(e)}")
            return """
            <div style="background-color: #ffebee; padding: 5px 10px; border-radius: 5px; display: inline-block;">
                Errore nel conteggio progetti
            </div>
            """

    def delete_project(self, project_display_name):
        """Elimina un progetto dal database"""
        if not project_display_name or project_display_name not in self.projects_data:
            return self.add_log("Nessun progetto selezionato")
    
        project_id = self.projects_data[project_display_name]
    
        try:
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Elimina prima le relazioni
            cursor.execute("DELETE FROM project_variables WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM project_results WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM incremental_responses WHERE project_id = ?", (project_id,))
        
            # Elimina il progetto
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        
            conn.commit()
            conn.close()
        
            return self.add_log(f"✅ Progetto {project_id} eliminato con successo")
    
        except Exception as e:
            return self.add_log(f"❌ Errore nell'eliminazione del progetto: {str(e)}")

    @safe_db_operation
    

    def search_projects(self, keyword=""):
        """Cerca progetti che contengono la keyword specificata"""
        try:
            if not keyword:
                return self.load_projects_list()
        
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Query per cercare progetti che contengono la keyword
            query = """
            SELECT 
                p.id, 
                p.name, 
                p.creation_date,
                (SELECT value FROM project_variables WHERE project_id = p.id AND name = 'KEYWORD' LIMIT 1) as keyword,
                (SELECT COUNT(DISTINCT prompt_id) FROM project_results WHERE project_id = p.id) as phases_count,
                (SELECT prompt_id FROM project_results WHERE project_id = p.id ORDER BY id DESC LIMIT 1) as last_phase,
                (SELECT COUNT(*) FROM project_results WHERE project_id = p.id) as results_count
            FROM projects p
            WHERE 
                p.name LIKE ? OR
                p.id IN (SELECT project_id FROM project_variables WHERE value LIKE ?)
            ORDER BY p.creation_date DESC
            """
        
            search_term = f"%{keyword}%"
            cursor.execute(query, (search_term, search_term))
            projects = cursor.fetchall()
            conn.close()
        
            # Formatta i risultati
            formatted_projects = []
            project_choices = []
            self.project_ids_by_index = []
            
            for proj in projects:
                proj_id = proj[0]
                proj_name = proj[1]
                date_str = proj[2]
                proj_keyword = proj[3] or "N/A"
                
                # Formatta la data
                try:
                    if date_str and isinstance(date_str, str):
                        if 'T' in date_str:  # Formato ISO
                            date_formatted = datetime.fromisoformat(date_str).strftime('%d/%m/%Y %H:%M')
                        else:
                            date_formatted = date_str
                    else:
                        date_formatted = str(date_str)
                except Exception:
                    date_formatted = str(date_str)
                
                # Display informativo
                display_name = f"{proj_name} - {proj_keyword} ({date_formatted})"
                
                project_data = {
                    "id": proj_id,
                    "name": proj_name,
                    "date": date_formatted,
                    "keyword": proj_keyword,
                    "display": display_name
                }
                
                formatted_projects.append(project_data)
                project_choices.append(display_name)
                self.project_ids_by_index.append(proj_id)
        
            # Salva progetti in dizionario per uso futuro
            self.projects_data = {p["display"]: p["id"] for p in formatted_projects}
            self.projects_details = {p["id"]: p for p in formatted_projects}
        
            self.add_log(f"🔍 Trovati {len(formatted_projects)} progetti contenenti '{keyword}'")
            return project_choices
        
        except Exception as e:
            self.add_log(f"❌ Errore nella ricerca progetti: {str(e)}")
            return []

    def get_database_stats(self):
        """Ottiene statistiche generali sul database"""
        try:
            conn = sqlite3.connect(self.project_db_path)
            cursor = conn.cursor()
        
            # Conta progetti totali
            cursor.execute("SELECT COUNT(*) FROM projects")
            total_projects = cursor.fetchone()[0]
        
            # Conta progetti per fase
            cursor.execute("""
                SELECT prompt_id, COUNT(DISTINCT project_id) as count 
                FROM project_results 
                GROUP BY prompt_id
                ORDER BY count DESC
            """)
            phase_stats = cursor.fetchall()
        
            # Statistiche cronologiche
            cursor.execute("""
                SELECT strftime('%Y-%m', creation_date) as month, COUNT(*) as count
                FROM projects
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            """)
            time_stats = cursor.fetchall()
        
            conn.close()
        
            # Formatta le statistiche
            stats_text = f"**Progetti totali:** {total_projects}\n\n"
        
            if phase_stats:
                stats_text += "**Progetti per fase:**\n"
                for phase, count in phase_stats:
                    stats_text += f"- {phase}: {count} progetti\n"
        
            if time_stats:
                stats_text += "\n**Trend ultimi mesi:**\n"
                for month, count in time_stats:
                    stats_text += f"- {month}: {count} progetti\n"
        
            return stats_text
        
        except Exception as e:
            return f"❌ Errore nel caricamento statistiche: {str(e)}"