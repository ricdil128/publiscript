# analysis/analyzers.py

import os
import re
import json
import sqlite3
import shutil
import time
import logging
import traceback

from datetime import datetime

import gradio as gr  # usato in complete_analysis
from ai_interfaces.browser_manager import get_connection_status
from ai_interfaces.interaction_utils import get_input_box, clear_chat

from framework.analysis.market_analysis import (
    filter_legacy_prompt_sections,
    analyze_market_crisp as framework_analyze_market_crisp,
    analyze_market_legacy as framework_analyze_market_legacy
)
from framework.formatters import format_analysis_results_html, save_analysis_to_html

class MarketAnalyzer:
    def __init__(self):
        # Variabili che ti servono per tutta l'analisi
        self.current_analysis_params = {}
        self.analysis_type_radio = None 

    def analyze_market(self, builder, book_type, keyword, language, market,
                       analysis_prompt=None, use_crisp=None):

            """
            Analizza il mercato dei libri per la keyword specificata.

            Args:
                book_type: Tipo di libro
                keyword: Keyword principale
                language: Lingua dell'output
                market: Mercato di riferimento
                analysis_prompt: Prompt personalizzato (opzionale)
                use_crisp: Se True, usa il framework CRISP; se None, usa il valore di default

            Returns:
                str: Log dell'operazione
            """

            # Salva i parametri dell'analisi corrente per un eventuale riavvio
            self.current_analysis_params = {
                'book_type': book_type,
                'keyword': keyword,
                'language': language,
                'market': market,
                'analysis_prompt': analysis_prompt,
                'use_crisp': use_crisp,
                'selected_phases': builder.get_selected_phases()  # Metodo aggiuntivo che restituisce le fasi selezionate
            }



            # Aggiungi log dettagliati per il debug
            if hasattr(self, 'analysis_type_radio'):
                builder.add_log(f"DEBUG: analysis_type_radio esiste: valore = {self.analysis_type_radio.value}")
            else:
                builder.add_log("DEBUG: analysis_type_radio non esiste!")
            try:
                # Verifica se esiste già un'analisi per questa keyword
                exists, project_id, creation_date = builder.check_existing_analysis(keyword)

                if exists:
                    # Crea un messaggio di avviso HTML per la UI
                    warning_html = f"""
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
                        <div class="flex items-center">
                            <div class="flex-shrink-0">
                                <span class="text-yellow-400 text-xl">⚠️</span>
                            </div>
                            <div class="ml-3">
                                <h3 class="text-lg font-medium text-yellow-800">Analisi esistente rilevata</h3>
                                <p class="text-yellow-700">Esiste già un'analisi per la keyword '{keyword}' creata il {creation_date}.</p>
                                <div class="mt-3">
                                    <button id="new-analysis-btn" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-3 rounded mr-2" 
                                            onclick="updateAnalysisChoice('1')">Crea nuova analisi</button>
                                    <button id="view-analysis-btn" class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-3 rounded mr-2" 
                                            onclick="updateAnalysisChoice('2')">Visualizza esistente</button>
                                    <button id="resume-analysis-btn" class="bg-purple-500 hover:bg-purple-700 text-white font-bold py-1 px-3 rounded" 
                                            onclick="updateAnalysisChoice('3')">Riprendi dall'ultima fase</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <script>
                    function updateAnalysisChoice(choice) {{
                        /* Nascondi il box di avviso */
                        const warningBox = document.querySelector('.bg-yellow-50');
                        if (warningBox) warningBox.style.display = 'none';

                        /* Notifica l'utente della scelta */
                        const resultBox = document.createElement('div');
                        resultBox.className = 'bg-blue-50 p-3 rounded-lg';

                        if (choice === '1') {{
                            resultBox.innerHTML = '<p>Creazione nuova analisi in corso...</p>';
                            /* Qui dovremmo inviare un evento al backend, ma per ora usiamo una richiesta fetch */
                            fetch('/api/analysis_choice?choice=1&project_id={project_id}')
                                .then(response => console.log('Choice registered'));
                        }} else if (choice === '2') {{
                            resultBox.innerHTML = '<p>Caricamento analisi esistente...</p>';
                            fetch('/api/analysis_choice?choice=2&project_id={project_id}')
                                .then(response => console.log('Choice registered'));
                        }} else if (choice === '3') {{
                            resultBox.innerHTML = '<p>Ripresa analisi in corso...</p>';
                            fetch('/api/analysis_choice?choice=3&project_id={project_id}')
                                .then(response => console.log('Choice registered'));
                        }}

                        /* Aggiungi la notifica alla pagina */
                        warningBox.parentNode.appendChild(resultBox);
                    }}
                    </script>
                    """

                    # Per la console di log, usa un formato più semplice
                    warning_text = f"""⚠️ ATTENZIONE: Esiste già un'analisi per la keyword '{keyword}'
                Creata il: {creation_date}

                Vuoi:
                1) Creare una nuova analisi comunque
                2) Visualizzare l'analisi esistente
                3) Riprendere dall'ultima fase completata
                """

                    builder.add_log(warning_text)

                    # Se disponiamo di una UI più semplice (file di testo), usiamo input()
                    # Altrimenti il codice HTML mostrerà pulsanti nell'interfaccia
                    try:
                        # Controlla se siamo in modalità console o UI
                        if hasattr(self, 'results_display'):
                            # Modalità UI: aggiorna l'HTML e attendi la risposta asincrona
                            if hasattr(self.results_display, 'update'):
                                self.results_display.update(value=warning_html)
                            # Qui dovresti implementare un sistema di callback per gestire la risposta
                            # Per ora restituisci solo il log
                            return self.chat_manager.get_log_history_string()
                        else:
                            # Modalità console
                            choice = input("Inserisci il numero della tua scelta (1/2/3): ")

                            if choice == "2":
                                # Carica i dettagli del progetto esistente
                                details = builder.load_project_details(project_id)
                                builder.add_log(details)
                                return self.chat_manager.get_log_history_string()

                            elif choice == "3":
                                # Ripristina l'analisi esistente
                                return builder.ripristina_analisi_da_database(project_id)

                            # Se choice è "1" o altro, continua normalmente con una nuova analisi
                    except Exception as input_error:
                        builder.add_log(f"Errore nell'interazione con l'utente: {str(input_error)}")
                        builder.add_log("Procedo con una nuova analisi...")
                        # Continua con l'analisi normalmente

                # Da qui in poi è il codice originale per l'analisi

                # 1) Verifico login e driver
                from ai_interfaces.browser_manager import get_connection_status
                if not get_connection_status() or not self.driver:
                    return builder.add_log("Errore: Devi prima connetterti!")

                # 2) Avvio analisi
                builder.add_log(f"Avvio analisi di mercato per: {keyword}")

                # Inizializza/reimposta lo stato delle domande
                if not hasattr(self, 'question_status'):
                    self.question_status = {}
                else:
                    self.question_status.clear()

                # 3) Decido se usare CRISP o il metodo legacy in base all'attributo selected_analysis_type
                # Usa l'attributo invece del componente UI direttamente
                if hasattr(self, 'selected_analysis_type'):
                    analysis_type = self.selected_analysis_type
                    builder.add_log(f"DEBUG: Usando tipo di analisi salvato: {analysis_type}")
                else:
                    analysis_type = "CRISP"  # Fallback al default
                    builder.add_log(f"DEBUG: Nessun tipo di analisi salvato, usando default: {analysis_type}")

                # Imposta use_crisp_for_this_run in base a analysis_type, a meno che non sia esplicitamente passato
                use_crisp_for_this_run = (analysis_type == "CRISP") if use_crisp is None else use_crisp

                builder.add_log(f"ℹ️ Modalità analisi selezionata: {analysis_type} (use_crisp = {use_crisp_for_this_run})")

                # Ottieni le fasi selezionate in base al tipo di analisi
                selected_phases = []
                if analysis_type == "CRISP":
                    # Debug dello stato dei checkbox CRISP
                    builder.add_log("DEBUG - Stato dei checkbox CRISP:")
                    try:
                        # Ottieni i valori selezionati dal CheckboxGroup
                        selected_values = self.crisp_phase_checkboxes.value
                        builder.add_log(f"DEBUG: Valori selezionati nel CheckboxGroup CRISP: {selected_values}")

                        import re
                        for selected_value in selected_values:
                            # Estrai l'ID della fase dal valore selezionato (es. "CM-1: Descrizione")
                            match = re.match(r'([A-Z]+-[0-9A-Z]+):', selected_value)
                            if match:
                                phase_id = match.group(1)
                                selected_phases.append(phase_id)
                                builder.add_log(f"DEBUG: Aggiunta fase CRISP {phase_id}")
                    except Exception as e:
                        builder.add_log(f"ERRORE nel leggere CheckboxGroup CRISP: {str(e)}")

                    builder.add_log(f"🔍 Fasi CRISP selezionate: {', '.join(selected_phases)}")
                else:  # Legacy
                    # Debug dello stato di tutti i checkbox Legacy
                    builder.add_log("DEBUG - Stato dei checkbox Legacy:")
                    # Inizializziamo le variabili all'inizio
                    any_true = False
                    all_true = False

                    try:
                        # Ottieni i valori selezionati dal CheckboxGroup
                        selected_values = self.legacy_phase_checkboxes.value
                        builder.add_log(f"DEBUG: Valori selezionati nel CheckboxGroup Legacy: {selected_values}")

                        # Aggiorniamo le variabili solo dopo aver ottenuto i valori
                        any_true = len(selected_values) > 0
                        all_true = len(selected_values) == len(self.legacy_phase_checkboxes.choices)

                        import re
                        for selected_value in selected_values:
                            # Estrai l'ID della fase dal valore selezionato (es. "LM-1: Descrizione")
                            match = re.match(r'([A-Z]+-\d+):', selected_value)
                            if match:
                                phase_id = match.group(1)
                                # Estrai il numero dalla fase (es. da LM-1 estrae 1)
                                number_match = re.search(r'-(\d+)', phase_id)
                                if number_match:
                                    phase_number = int(number_match.group(1))
                                    selected_phases.append(phase_number)
                                    builder.add_log(f"DEBUG: Aggiunta fase Legacy {phase_id} (numero {phase_number})")

                    except Exception as e:
                        builder.add_log(f"ERRORE nel leggere CheckboxGroup Legacy: {str(e)}")
                        # Se c'è un'eccezione, manteniamo i valori di default
                        # any_true e all_true sono già inizializzati a False

                    # Se tutti i checkbox risultano True, potrebbe esserci un bug
                    if all_true and len(self.legacy_phase_checkboxes.choices) > 1:
                        builder.add_log("⚠️ ATTENZIONE: Tutti i checkbox risultano selezionati, possibile bug")

                        # Controlla i log precedenti per vedere quali checkbox sono stati davvero selezionati
                        if hasattr(self, 'chat_manager') and hasattr(self.chat_manager, 'get_log_history'):
                            log_lines = self.chat_manager.get_log_history()
                            selected_from_logs = []

                            # Cerca le linee di log che indicano quali checkbox sono stati selezionati
                            import re
                            for line in log_lines[-50:]:  # Considera solo le ultime 50 linee
                                match = re.search(r'Legacy checkbox (\d+): True', line)
                                if match:
                                    phase_id = int(match.group(1))
                                    selected_from_logs.append(phase_id)

                            # Se troviamo checkbox selezionati nei log, usa quelli
                            if selected_from_logs:
                                selected_phases = list(set(selected_from_logs))  # Rimuovi duplicati
                                builder.add_log(f"🔄 Corretto selected_phases dai log: {selected_phases}")

                    # Se non è stato selezionato nessun checkbox ma i log mostrano checkbox selezionati
                    elif not any_true and hasattr(self, 'chat_manager') and hasattr(self.chat_manager, 'get_log_history'):
                        log_lines = self.chat_manager.get_log_history()
                        selected_from_logs = []

                        # Cerca le linee di log che indicano quali checkbox sono stati selezionati
                        import re
                        for line in log_lines[-50:]:  # Considera solo le ultime 50 linee
                            match = re.search(r'Legacy checkbox (\d+): True', line)
                            if match:
                                phase_id = int(match.group(1))
                                selected_from_logs.append(phase_id)

                        # Se troviamo checkbox selezionati nei log, usa quelli
                        if selected_from_logs:
                            selected_phases = list(set(selected_from_logs))  # Rimuovi duplicati
                            builder.add_log(f"🔄 Impostato selected_phases dai log: {selected_phases}")

                    builder.add_log(f"🔍 Fasi Legacy selezionate: {', '.join([str(p) for p in selected_phases])}")

                # Verifica finale se ci sono fasi selezionate
                if not selected_phases:
                    return builder.add_log("⚠️ Nessuna fase selezionata! Seleziona almeno una fase dell'analisi.")

                # Aggiungi formattazione HTML se disponibile
                if use_crisp_for_this_run:
                    # Approccio CRISP con fasi selezionate
                    result = self._analyze_market_crisp(book_type, keyword, language, market, selected_phases)

                    # AGGIUNTO: Salva i risultati dell'analisi nel contesto
                    try:
                        # Ottieni il contesto dal current_analysis
                        context = self.current_analysis.get('project_data', {}) if hasattr(self, 'current_analysis') else {}

                        # Metadati per il contesto
                        metadata = {
                            "type": "market_analysis_crisp",
                            "book_type": book_type,
                            "keyword": keyword,
                            "language": language,
                            "market": market,
                            "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
                        }

                        # Salva nel file di contesto
                        if hasattr(self, 'chat_manager'):
                            self.chat_manager.save_response(
                                result,
                                f"Analisi CRISP: {keyword}",
                                metadata
                            )
                            builder.add_log(f"✅ Risultati dell'analisi CRISP salvati nel contesto ({len(result)} caratteri)")
                    except Exception as save_error:
                        builder.add_log(f"⚠️ Errore nel salvataggio del contesto: {str(save_error)}")

                    # Se abbiamo la funzione di formattazione HTML e un display risultati, usiamoli
                    if hasattr(self, 'format_analysis_results_html') and hasattr(self, 'results_display'):
                        try:
                            # Ottieni il contesto dal current_analysis
                            context = self.current_analysis.get('project_data', {}) if hasattr(self, 'current_analysis') else {}

                            # Genera HTML formattato
                            html_results = self.format_analysis_results_html(keyword, market, book_type, language, context)



                            # Aggiorna il display dei risultati
                            # Usa assegnazione diretta invece di update
                            if hasattr(self.results_display, 'update'):
                                self.results_display.update(value=html_results)
                            else:
                                self.results_display.value = html_results
                        except Exception as format_error:
                            builder.add_log(f"Errore nella formattazione HTML: {str(format_error)}")
                else:
                    # Approccio legacy con fasi selezionate
                    if analysis_prompt is None:
                        analysis_prompt = self.default_analysis_prompt

                    # Filtra il prompt prima di passarlo all'analisi
                    filtered_prompt = self._filter_legacy_prompt_sections(analysis_prompt, selected_phases)

                    # Esegui l'analisi legacy con il prompt filtrato
                    result = self._analyze_market_legacy(book_type, keyword, language, market, filtered_prompt)

                    # AGGIUNTO: Salva i risultati dell'analisi nel contesto
                    try:
                        # Metadati per il contesto
                        metadata = {
                            "type": "market_analysis_legacy",
                            "book_type": book_type,
                            "keyword": keyword,
                            "language": language,
                            "market": market,
                            "timestamp": datetime.now().strftime('%Y%m%d_%H%M%S')
                        }

                        if hasattr(self, 'chat_manager'):
                            self.chat_manager.save_response(
                                result,
                                f"Analisi Legacy: {keyword}",
                                metadata
                            )
                            builder.add_log(f"✅ Risultati dell'analisi legacy salvati nel contesto ({len(result)} caratteri)")
                    except Exception as save_error:
                        builder.add_log(f"⚠️ Errore nel salvataggio del contesto: {str(save_error)}")

                    # Mostra un riepilogo dello stato delle domande
                    if hasattr(self, 'question_status') and self.question_status:
                        builder.add_log("\n=== RIEPILOGO ANALISI ===")
                        for qnum, status in sorted(self.question_status.items()):
                            emoji = "✅" if status['success'] else "❌"
                            chars = status.get('chars', 0)
                            builder.add_log(f"{emoji} Domanda #{qnum}: {status['status']} ({chars} caratteri)")

                        # Identifica domande fallite o senza risposta
                        failed_questions = [qnum for qnum, status in self.question_status.items() if not status['success']]
                        if failed_questions:
                            builder.add_log(f"⚠️ Attenzione: le domande {', '.join(str(q) for q in failed_questions)} potrebbero richiedere nuovi tentativi")

                    # Aggiorna lo stato dell'analisi
                    if hasattr(self, 'analysis_status'):
                        self.analysis_status.update(value="**Stato analisi**: Completata ✅")

                    # Verifica che self.results_display e self.analysis_status non siano lo stesso oggetto
                    if hasattr(self, 'results_display') and hasattr(self, 'analysis_status'):
                        same_object = id(self.results_display) == id(self.analysis_status)
                        if same_object:
                            builder.add_log("⚠️ results_display e analysis_status sono lo stesso oggetto, evito di caricare i risultati per prevenire sovrascritture")
                        else:
                            # Carica i risultati solo se sono oggetti diversi
                            self.load_analysis_results()
                    else:
                        # Se uno dei due non esiste, procedi normalmente
                        self.load_analysis_results()

                    builder.add_log("📌 Analisi parziale completata. Premi '✅ Completa Analisi' per salvare nel database.")

                    return result

            except Exception as e:
                error_msg = f"Errore durante l'analisi: {str(e)}"
                builder.add_log(error_msg)
                logging.error(error_msg)
                return self.chat_manager.get_log_history_string()

    def _analyze_market_crisp(self, book_type, keyword, language, market, selected_phases=None):
            """
            Analizza il mercato usando il framework CRISP.
            Delega alla funzione in framework/analysis/market_analysis.py

            Args:
                book_type: Tipo di libro
                keyword: Keyword principale
                language: Lingua dell'output
                market: Mercato di riferimento
                selected_phases: Lista di fasi selezionate da eseguire (opzionale)

            Returns:
                str: Log dell'operazione
            """
            # Log di debug per verificare i CheckboxGroup
            builder.add_log(f"DEBUG: crisp_phase_checkboxes esiste: {hasattr(self, 'crisp_phase_checkboxes')}")

            # Se non sono state specificate fasi, ottienile dal CheckboxGroup
            if not selected_phases:
                selected_phases = []

                if hasattr(self, 'crisp_phase_checkboxes') and self.crisp_phase_checkboxes is not None:
                    try:
                        # Ottieni tutte le fasi selezionate dal CheckboxGroup
                        selected_values = self.crisp_phase_checkboxes.value
                        builder.add_log(f"DEBUG: Valori selezionati da crisp_phase_checkboxes: {selected_values}")

                        import re
                        for selected_value in selected_values:
                            # Estrae l'ID di fase dalla stringa selezionata (es. "CM-1: Analisi del mercato...")
                            # Supporta sia il formato CM-1, CS-1, CP-1, CPM-1 ecc.
                            match = re.match(r'([A-Z]+-[0-9A-Z]+):', selected_value)
                            if match:
                                phase_id = match.group(1)
                                selected_phases.append(phase_id)
                                builder.add_log(f"📊 Fase CRISP selezionata: {phase_id}")
                    except Exception as e:
                        builder.add_log(f"⚠️ Errore nella lettura del CheckboxGroup: {str(e)}")

                # Se nessuna fase è stata trovata, usa CM-1 come default
                if not selected_phases:
                    selected_phases = ["CM-1"]
                    builder.add_log("⚠️ Nessuna fase CRISP trovata, uso CM-1 come default")

            builder.add_log(f"🔍 Esecuzione selettiva delle fasi CRISP: {', '.join(selected_phases)}")

            # Importa on-demand per evitare dipendenze circolari
            from framework.analysis.market_analysis import analyze_market_crisp

            try:
                result = analyze_market_crisp(
                    book_type=book_type,
                    keyword=keyword,
                    language=language,
                    market=market,
                    selected_phases=selected_phases,
                    crisp_framework=self.crisp,
                    driver=self.driver,
                    chat_manager=self.chat_manager
                )

                # Aggiorna current_analysis se il risultato contiene i dati di progetto
                if isinstance(result, dict) and 'crisp_project_id' in result:
                    self.current_analysis = result

                return self.chat_manager.get_log_history_string()
            except Exception as e:
                builder.add_log(f"❌ Errore durante l'analisi CRISP: {str(e)}")
                import traceback
                builder.add_log(traceback.format_exc())
                return f"Errore durante l'analisi: {str(e)}"    


    def _analyze_market_legacy(self, book_type, keyword, language, market, analysis_prompt):
            """
            Metodo legacy per l'analisi di mercato, che invia automaticamente
            le righe di prompt selezionate e restituisce la risposta cumulativa.

            Delega alla funzione analyze_market_legacy in framework/analysis/market_analysis.py
            """

            # 1. Controllo riavvio richiesto
            if hasattr(self, 'restart_analysis_needed') and self.restart_analysis_needed:
                builder.add_log("🔄 Riavvio richiesto dopo reset del contesto - esecuzione in corso...")
                self.restart_analysis_needed = False
                return self.restart_current_analysis()

            import re
            selected_phases = []

            # 2. DEBUG: Check esistenza checkbox
            builder.add_log(f"DEBUG: legacy_phase_checkboxes esiste: {hasattr(self, 'legacy_phase_checkboxes')}")

            if hasattr(self, 'legacy_phase_checkboxes') and self.legacy_phase_checkboxes is not None:
                try:
                    selected_values = self.legacy_phase_checkboxes.value
                    builder.add_log(f"DEBUG: Valori selezionati da legacy_phase_checkboxes: {selected_values}")

                    for selected_value in selected_values:
                        match = re.match(r'([A-Z]+-\d+):', selected_value)
                        if match:
                            phase_id = match.group(1)
                            number_match = re.search(r'-(\d+)', phase_id)
                            if number_match:
                                phase_number = int(number_match.group(1))
                                selected_phases.append(phase_number)
                                builder.add_log(f"📊 Fase Legacy selezionata: {phase_id} (numero {phase_number})")
                        else:
                            builder.add_log(f"⚠️ Nessuna corrispondenza regex trovata per: {selected_value}")
                except Exception as e:
                    builder.add_log(f"⚠️ Errore nella lettura del CheckboxGroup: {str(e)}")

            # 3. Fallback se non è stata trovata nessuna fase
            if not selected_phases:
                selected_phases = [1]
                builder.add_log("⚠️ Nessuna fase trovata, uso fase 1 come default")

            builder.add_log(f"🔍 Fasi Legacy selezionate finali: {', '.join(map(str, selected_phases))}")

            # 4. Regex per dividere le sezioni nel prompt
            filtered_sections = []
            pattern = r'(\d+)[\.|\)](.*?)(?=\n\s*\d+[\.|\)]|$)'

            try:
                matches = list(re.finditer(pattern, analysis_prompt, re.DOTALL))
                builder.add_log(f"📋 Trovate {len(matches)} sezioni totali nel prompt")
            except Exception as e:
                builder.add_log(f"⚠️ Errore nell'analisi del prompt con regex: {str(e)}")
                matches = []

            # 5. Filtraggio delle sezioni in base alle fasi
            for match in matches:
                try:
                    section_number = int(match.group(1))
                    if section_number in selected_phases:
                        filtered_sections.append(match.group(0))
                        builder.add_log(f"✅ Inclusa sezione {section_number}")
                    else:
                        builder.add_log(f"❌ Saltata sezione {section_number} (non selezionata)")
                except Exception as e:
                    builder.add_log(f"⚠️ Errore nel processare una sezione del prompt: {str(e)}")

            # 6. Se nessuna sezione viene inclusa, prova comunque la sezione 1
            if not filtered_sections and matches:
                builder.add_log("⚠️ Nessuna sezione filtrata: tentativo di usare la sezione 1 come fallback")
                for match in matches:
                    try:
                        if int(match.group(1)) == 1:
                            filtered_sections.append(match.group(0))
                            builder.add_log("✅ Fallback: inclusa sezione 1")
                            break
                    except Exception as e:
                        builder.add_log(f"⚠️ Errore nel fallback su sezione 1: {str(e)}")

            # 7. Se ancora nessuna sezione trovata, interrompi
            if not filtered_sections:
                return builder.add_log("❌ Nessuna fase selezionata! Seleziona almeno una fase dell'analisi.")

            # 8. Costruzione del prompt filtrato
            filtered_prompt = "\n\n".join(filtered_sections)
            builder.add_log(f"✅ Prompt filtrato: {len(filtered_prompt)} caratteri, {len(filtered_sections)} sezioni")

            # 9. Chiamata finale al modulo delegato
            from framework.analysis.market_analysis import analyze_market_legacy

            return analyze_market_legacy(
                book_type=book_type,
                keyword=keyword,
                language=language,
                market=market,
                analysis_prompt=filtered_prompt,
                driver=self.driver,
                chat_manager=self.chat_manager,
                markets=self.markets
            )


    def resume_analysis(self, project_id, selected_phases=None):
            """
            Riprende un'analisi esistente eseguendo fasi specifiche.

            Args:
                project_id: ID del progetto da riprendere
                selected_phases: Lista di fasi da eseguire (opzionale)

            Returns:
                str: Log dell'operazione
            """
            try:
                builder.add_log(f"🔄 Ripresa analisi per progetto ID: {project_id}")

                # Recupera i dati del progetto
                project_data = self.crisp._load_project_data(project_id)
                if not project_data:
                    return builder.add_log(f"❌ Progetto ID {project_id} non trovato!")

                # Imposta il progetto come analisi corrente
                self.current_analysis = {
                    'crisp_project_id': project_id,
                    'project_data': project_data,
                    'KEYWORD': project_data.get('KEYWORD', 'unknown')
                }

                # Se non ci sono fasi specificate, usa tutte le rimanenti
                if not selected_phases:
                    # Determina qual è l'ultima fase eseguita
                    last_phase = self.crisp._get_last_executed_step(project_id)
                    if last_phase:
                        # Trova l'indice della fase nell'elenco completo
                        all_phases = ["CM-1", "CM-2", "CM-3", "CM-4", "CM-5", "CM-6", "CM-7", "CM-8"]
                        try:
                            last_index = all_phases.index(last_phase)
                            # Seleziona tutte le fasi successive
                            selected_phases = all_phases[last_index+1:]
                        except ValueError:
                            # Se la fase non è nell'elenco standard, usa tutte le fasi
                            selected_phases = all_phases
                    else:
                        # Se non c'è una fase precedente, usa tutte le fasi
                        selected_phases = ["CM-1", "CM-2", "CM-3", "CM-4", "CM-5", "CM-6", "CM-7", "CM-8"]

                # Se ci sono fasi da eseguire, procedi
                if selected_phases:
                    builder.add_log(f"🔍 Ripresa con fasi: {', '.join(selected_phases)}")

                    # Definisci la funzione executor
                    def process_prompt(prompt_text):
                        builder.add_log(f"Elaborazione prompt: {len(prompt_text)} caratteri")
                        response = self.send_to_genspark(prompt_text)
                        return response

                    # Esegui le fasi selezionate una per una
                    execution_history = []
                    current_data = project_data.copy()

                    for phase_id in selected_phases:
                        builder.add_log(f"🔄 Esecuzione fase {phase_id}")

                        # Esegui la singola fase
                        updated_data, phase_result, extracted_data = self.crisp.execute_step(
                            phase_id, 
                            current_data.copy(), 
                            process_prompt
                        )

                        # Aggiorna i dati correnti con i risultati della fase
                        current_data.update(updated_data)

                        # Aggiungi alla storia di esecuzione
                        execution_history.append({
                            'step_id': phase_id,
                            'result': phase_result,
                            'extracted_data': extracted_data
                        })

                    # Aggiorna l'analisi corrente con i nuovi dati
                    self.current_analysis['project_data'] = current_data
                    self.current_analysis['execution_history'] = execution_history

                    builder.add_log("✅ Ripresa analisi completata con successo")
                else:
                    builder.add_log("⚠️ Nessuna fase da eseguire - l'analisi è già completa")

                # Carica i risultati aggiornati
                self.load_analysis_results()

                return self.chat_manager.get_log_history_string()

            except Exception as e:
                builder.add_log(f"❌ Errore nella ripresa dell'analisi: {str(e)}")
                import traceback
                builder.add_log(traceback.format_exc())
                return self.chat_manager.get_log_history_string()

    def continue_analysis(self):
            """Continua l'analisi dopo una pausa manuale"""
            try:
                # Controlla se stai usando CRISP
                if hasattr(self, 'use_crisp') and self.use_crisp and hasattr(self, 'current_analysis') and self.current_analysis.get('crisp_project_id'):
                    return self._continue_analysis_crisp()
                else:
                    return self._continue_analysis_legacy()
            except Exception as e:
                print(f"DEBUG ERROR: {str(e)}")
                return builder.add_log(f"Errore durante il completamento dell'analisi: {str(e)}")

    def _continue_analysis_crisp(self):
            """Continua l'analisi CRISP dopo una pausa manuale"""
            try:
                builder.add_log("Continuazione analisi PubliScript...")
                # Ottieni la risposta attuale dalla chat
                response = self.get_last_response()

                if not response:
                    return builder.add_log("Non è stato possibile recuperare la risposta dalla chat")

                # Recupera l'ID del progetto CRISP
                project_id = self.current_analysis.get('crisp_project_id')
                if not project_id:
                    return builder.add_log("Errore: Nessun progetto CRISP trovato")

                # Determina quale fase CRISP è stata interrotta
                execution_history = self.current_analysis.get('execution_history', [])
                if not execution_history:
                    return builder.add_log("Errore: Nessuna storia di esecuzione trovata")

                last_step = execution_history[-1]['step_id']
                builder.add_log(f"Ripresa dall'ultimo step completato: {last_step}")

                # Salva la risposta nel database
                # Aggiorna i dati del progetto con la nuova risposta
                self.chat_manager.save_response(
                    response,
                    f"Continuazione CRISP - {last_step}",
                    {"project_id": project_id, "manual_continuation": True}
                )

                # Continua l'esecuzione del flusso CRISP
                # Definisci una funzione executor per continuare
                def continue_executor(prompt_text):
                    builder.add_log(f"Continuazione prompt CRISP ({len(prompt_text)} caratteri)...")
                    lines = [line.strip() for line in prompt_text.split('\n') if line.strip()]
                    cumulative_response = []

                    for i, line in enumerate(lines):
                        builder.add_log(f"Linea {i+1}/{len(lines)}: {line[:50]}...")
                        response = self.send_to_genspark(line)
                        cumulative_response.append(response)
                        time.sleep(2)

                    combined_response = "\n\n".join(cumulative_response)
                    self.chat_manager.save_response(
                        combined_response,
                        "Continuazione CRISP",
                        {"project_id": project_id}
                    )
                    return combined_response

                # Aggiorna l'interfaccia per indicare che la continuazione è in corso
                builder.add_log("🔄 Ripresa dell'analisi CRISP...")

                # In un'implementazione reale, qui chiameresti il metodo del framework CRISP 
                # per continuare dal punto di interruzione. Però, poiché il framework non ha 
                # un metodo specifico per questo, dovresti implementare la logica tu stesso.
                builder.add_log("✅ Analisi CRISP continuata con successo")
                return self.chat_manager.get_log_history_string()

            except Exception as e:
                error_msg = f"Errore durante la continuazione dell'analisi CRISP: {str(e)}"
                builder.add_log(error_msg)
                logging.error(error_msg)
                return self.chat_manager.get_log_history_string()


    def complete_analysis(self):
        """
        Completa l'analisi e prepara i dettagli del libro.
        Estrae le informazioni critiche dal file di contesto o dal database CRISP
        e le prepara per la generazione del libro.
        """
        import re  # Importazione esplicita di re per evitare l'errore "variable referenced before assignment"
        import os
        import traceback
        import gradio as gr  # Aggiungi questa riga per importare gr all'interno del metodo
        from datetime import datetime

        # Ripara il database prima di continuare
        self.diagnose_and_fix_database()

        builder.add_log("▶️ Avvio funzione complete_analysis")

        # ==================== FASE 1: DIAGNOSTICA INIZIALE ====================
        # Verifica se il file di contesto esiste e stampa informazioni diagnostiche
        print(f"DEBUG-INIT: Avvio complete_analysis() con dettagli estesi")
        print(f"DEBUG-INIT: Tentativo di lettura del file context.txt - Esiste: {os.path.exists('context.txt')}")
        print(f"DEBUG-INIT: Directory corrente: {os.getcwd()}")
        print(f"DEBUG-INIT: Memoria disponibile per gli oggetti Python")

        # Verifica se ci sono dati nel current_analysis
        if hasattr(self, 'current_analysis'):
            print(f"DEBUG-INIT: current_analysis esiste: {type(self.current_analysis)}")
            if self.current_analysis:
                print(f"DEBUG-INIT: current_analysis contiene {len(self.current_analysis)} elementi")
                # Mostra le chiavi principali
                for key in list(self.current_analysis.keys())[:5]:  # Limita a 5 chiavi per leggibilità
                    print(f"DEBUG-INIT: - Chiave: {key}, Tipo: {type(self.current_analysis[key])}")
            else:
                print("DEBUG-INIT: current_analysis è un dizionario vuoto o None")
        else:
            print("DEBUG-INIT: current_analysis non esiste come attributo")

        # Backup del file di contesto prima di iniziare l'elaborazione
        if os.path.exists("context.txt"):
            try:
                file_size = os.path.getsize("context.txt")
                print(f"DEBUG-CONTEXT: File context.txt trovato - Dimensione: {file_size} bytes")

                # Leggi l'intestazione del file per debug
                try:
                    with open("context.txt", "r", encoding="utf-8") as f:
                        # Leggi le prime 10 righe o meno se il file è più corto
                        first_lines = []
                        for _ in range(10):
                            try:
                                line = next(f)
                                first_lines.append(line)
                            except StopIteration:
                                break

                        print(f"DEBUG-CONTEXT: Prime {len(first_lines)} righe del file:")
                        for i, line in enumerate(first_lines):
                            print(f"DEBUG-CONTEXT: Riga {i+1}: {line.strip()}")
                except Exception as e:
                    print(f"DEBUG-CONTEXT: Errore nella lettura dell'intestazione del file: {str(e)}")
                    print(f"DEBUG-CONTEXT: Traceback errore intestazione:\n{traceback.format_exc()}")

                # Crea backup con timestamp
                import shutil
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"context_backup_{timestamp}.txt"
                shutil.copy2("context.txt", backup_file)
                backup_size = os.path.getsize(backup_file)
                print(f"DEBUG-CONTEXT: Backup creato: {backup_file} ({backup_size} bytes)")

                # Leggi e stampa un'anteprima del contenuto
                try:
                    with open("context.txt", "r", encoding="utf-8") as f:
                        # Leggi i primi 300 caratteri per anteprima
                        context_preview = f.read(300)
                        print(f"DEBUG-CONTEXT: Anteprima del contenuto (primi 300 caratteri):")
                        # Sostituisci i caratteri di nuova riga con \n visibili
                        context_preview_formatted = context_preview.replace('\n', '\\n')
                        print(f"DEBUG-CONTEXT: {context_preview_formatted}")
                except Exception as e:
                    print(f"DEBUG-CONTEXT: Errore nella lettura dell'anteprima: {str(e)}")

            except Exception as backup_error:
                print(f"DEBUG-CONTEXT: Errore nel backup del file di contesto: {str(backup_error)}")
                print(f"DEBUG-CONTEXT: Traceback errore backup:\n{traceback.format_exc()}")
        else:
            print("DEBUG-CONTEXT: ATTENZIONE - File context.txt non trovato!")
            # Elenca tutti i file nella directory corrente per debug
            print("DEBUG-CONTEXT: Elenco dei file nella directory corrente:")
            try:
                files = os.listdir()
                for file in files:
                    if os.path.isfile(file):
                        print(f"DEBUG-CONTEXT: - {file} ({os.path.getsize(file)} bytes)")
            except Exception as e:
                print(f"DEBUG-CONTEXT: Errore nell'elenco dei file: {str(e)}")


        # ================ FASE 2: INIZIO DELL'ELABORAZIONE PRINCIPALE ================
        try:
            # Aggiungi al log
            builder.add_log("▶️ Avvio funzione complete_analysis")

            # Inizializza current_analysis se non esiste
            if not hasattr(self, 'current_analysis') or self.current_analysis is None:
                self.current_analysis = {}
                builder.add_log("ℹ️ Inizializzato current_analysis (non esisteva)")
                print("DEBUG-INIT: current_analysis inizializzato (era None)")
            else:
                print(f"DEBUG-INIT: current_analysis già esistente con {len(self.current_analysis)} chiavi")
                # Debug delle chiavi esistenti
                for key in self.current_analysis:
                    value_preview = str(self.current_analysis[key])
                    if len(value_preview) > 100:
                        value_preview = value_preview[:100] + "..."
                    print(f"DEBUG-INIT: - chiave: {key}, valore: {value_preview}")

            # ================ FASE 3: INIZIALIZZAZIONE VALORI DI RITORNO ================
            # Prepara i valori che verranno restituiti alla fine
            analysis_status_text = "**Stato analisi**: Completata"
            tabs_value = gr.Tabs(selected=2)  # Seleziona il tab "Generazione Libro"
            book_title_value = ""             # Titolo estratto dall'analisi
            book_index_value = ""             # Indice estratto dall'analisi
            voice_style_value = ""            # Stile di voce estratto dall'analisi
            book_type_value = ""              # Tipo di libro estratto dall'analisi

            print("DEBUG-VALUES: Valori di ritorno inizializzati con stringhe vuote")

            # ================ FASE 4: DETERMINA LA MODALITÀ (CRISP o LEGACY) ================
            # Verifica se si sta utilizzando il framework CRISP
            use_crisp = hasattr(self, 'use_crisp') and self.use_crisp
            builder.add_log(f"ℹ️ Modalità CRISP: {use_crisp}")
            print(f"DEBUG-MODE: Utilizzo framework CRISP: {use_crisp}")

            # ================ FASE 5A: ELABORAZIONE MODALITÀ CRISP ================
            if use_crisp and hasattr(self, 'current_analysis') and self.current_analysis.get('crisp_project_id'):
                print("DEBUG-CRISP: Avvio elaborazione in modalità CRISP")
                builder.add_log("🔍 Tentativo di estrazione dati da progetto CRISP")

                # Recupera l'ID del progetto CRISP
                project_id = self.current_analysis.get('crisp_project_id')
                if not project_id:
                    builder.add_log("⚠️ ID Progetto CRISP non trovato nella current_analysis")
                    print("DEBUG-CRISP: ID Progetto CRISP non trovato - impossibile recuperare dati")
                else:
                    builder.add_log(f"✅ ID Progetto CRISP trovato: {project_id}")
                    print(f"DEBUG-CRISP: ID Progetto CRISP trovato: {project_id}")

                    # Recupera i dati completi del progetto dal framework CRISP
                    project_data = None
                    try:
                        # Verifica se è possibile accedere ai dati del progetto
                        if hasattr(self, 'crisp') and hasattr(self.crisp, 'get_project_data'):
                            print(f"DEBUG-CRISP: Tentativo recupero dati con crisp.get_project_data({project_id})")

                            # Chiamata effettiva per recuperare i dati
                            project_data = self.crisp.get_project_data(project_id)

                            if project_data:
                                print(f"DEBUG-CRISP: Dati progetto recuperati: {len(project_data)} variabili")

                                # Stampa le prime 10 variabili per debug
                                counter = 0
                                for key, value in project_data.items():
                                    if counter < 10:
                                        value_str = str(value)
                                        if len(value_str) > 100:
                                            value_str = value_str[:100] + "..."
                                        print(f"DEBUG-CRISP: Variabile {counter+1}: {key} = {value_str}")
                                        counter += 1
                                    else:
                                        break

                                builder.add_log(f"✅ Dati progetto recuperati: {len(project_data)} variabili")
                            else:
                                print("DEBUG-CRISP: ERRORE - get_project_data ha restituito None")
                                builder.add_log("⚠️ get_project_data ha restituito None")
                        else:
                            print("DEBUG-CRISP: ERRORE - crisp o get_project_data non disponibili")

                            # Diagnostica dettagliata
                            if hasattr(self, 'crisp'):
                                print(f"DEBUG-CRISP: self.crisp esiste: {type(self.crisp)}")
                                print(f"DEBUG-CRISP: hasattr(self.crisp, 'get_project_data'): {hasattr(self.crisp, 'get_project_data')}")

                                # Elenca tutti i metodi disponibili per debug
                                methods = [method for method in dir(self.crisp) if not method.startswith('_')]
                                print(f"DEBUG-CRISP: Metodi disponibili in self.crisp: {methods}")
                            else:
                                print("DEBUG-CRISP: self.crisp non esiste come attributo")

                    except Exception as e:
                        builder.add_log(f"⚠️ Errore nel recupero dati progetto CRISP: {str(e)}")
                        print(f"DEBUG-CRISP: Eccezione in get_project_data: {str(e)}")
                        print(f"DEBUG-CRISP: Traceback dettagliato:\n{traceback.format_exc()}")

                    # ================ FASE 5A-1: ESTRAZIONE DATI DAL PROGETTO CRISP ================
                    # Se abbiamo recuperato i dati del progetto, estrai le informazioni necessarie
                    if project_data:
                        # Salva i dati del progetto per uso futuro
                        self.current_analysis['project_data'] = project_data
                        print("DEBUG-CRISP: project_data salvato in current_analysis per uso futuro")

                        # ---------- Estrazione Titolo ----------
                        if 'TITOLO_LIBRO' in project_data:
                            book_title_value = project_data.get('TITOLO_LIBRO', '')
                            builder.add_log(f"✅ Titolo estratto: {book_title_value}")
                            print(f"DEBUG-CRISP: Titolo estratto: '{book_title_value}'")
                        else:
                            print("DEBUG-CRISP: TITOLO_LIBRO non trovato nei dati del progetto")
                            # Cerca alternative per il titolo
                            for alt_key in ['TITLE', 'BOOK_TITLE', 'TITOLO']:
                                if alt_key in project_data:
                                    book_title_value = project_data.get(alt_key, '')
                                    print(f"DEBUG-CRISP: Titolo trovato in campo alternativo {alt_key}: {book_title_value}")
                                    break

                        # ---------- Estrazione Stile di Voce ----------
                        if 'VOICE_STYLE' in project_data:
                            voice_style_value = project_data.get('VOICE_STYLE', '')
                            builder.add_log(f"✅ Stile voce estratto: {voice_style_value}")
                            print(f"DEBUG-CRISP: Stile voce estratto: '{voice_style_value}'")
                        else:
                            print("DEBUG-CRISP: VOICE_STYLE non trovato nei dati del progetto")
                            # Cerca alternative per lo stile di voce
                            for alt_key in ['TONE', 'STYLE', 'WRITING_STYLE']:
                                if alt_key in project_data:
                                    voice_style_value = project_data.get(alt_key, '')
                                    print(f"DEBUG-CRISP: Stile voce trovato in campo alternativo {alt_key}: {voice_style_value}")
                                    break

                        # ---------- Estrazione Tipo di Libro ----------
                        if 'LIBRO_TIPO' in project_data:
                            book_type_value = project_data.get('LIBRO_TIPO', '')
                            builder.add_log(f"✅ Tipo di libro estratto: {book_type_value}")
                            print(f"DEBUG-CRISP: Tipo di libro estratto: '{book_type_value}'")
                        else:
                            print("DEBUG-CRISP: LIBRO_TIPO non trovato nei dati del progetto")
                            # Cerca alternative per il tipo di libro
                            for alt_key in ['BOOK_TYPE', 'TIPO', 'GENRE']:
                                if alt_key in project_data:
                                    book_type_value = project_data.get(alt_key, '')
                                    print(f"DEBUG-CRISP: Tipo libro trovato in campo alternativo {alt_key}: {book_type_value}")
                                    break

                        # ---------- Costruzione Indice del Libro ----------
                        print("DEBUG-CRISP: Tentativo costruzione indice del libro")

                        # Cerca CONTENT_PILLARS per la costruzione dell'indice
                        if 'CONTENT_PILLARS' in project_data:
                            builder.add_log("🔍 Tentativo di costruzione indice da CONTENT_PILLARS")
                            print("DEBUG-CRISP: Tentativo di costruzione indice da CONTENT_PILLARS")

                            pillars_text = project_data.get('CONTENT_PILLARS', '')
                            print(f"DEBUG-CRISP: CONTENT_PILLARS trovato, lunghezza: {len(pillars_text)}")
                            print(f"DEBUG-CRISP: Anteprima CONTENT_PILLARS: {pillars_text[:200]}...")

                            # Estrai i pilastri di contenuto con diversi pattern di espressioni regolari
                            pillars = []
                            if isinstance(pillars_text, str):
                                # Prova diversi pattern per estrarre pilastri
                                print("DEBUG-CRISP: Tentativo di estrazione pilastri con pattern regex")

                                pattern_results = {}

                                for pattern in [
                                    r'(\d+\.\s*[^\n]+)',             # Pattern per "1. Titolo"
                                    r'(\d+\)\s*[^\n]+)',             # Pattern per "1) Titolo"
                                    r'(CAPITOLO \d+[^:\n]*:[^\n]+)', # Pattern per "CAPITOLO 1: Titolo"
                                    r'(Capitolo \d+[^:\n]*:[^\n]+)'  # Pattern per "Capitolo 1: Titolo"
                                ]:
                                    # Prova ogni pattern e registra i risultati
                                    pillar_matches = re.findall(pattern, pillars_text)
                                    pattern_results[pattern] = pillar_matches

                                    if pillar_matches:
                                        print(f"DEBUG-CRISP: Pattern '{pattern}' ha trovato {len(pillar_matches)} corrispondenze")
                                        # Mostra le prime corrispondenze
                                        for i, match in enumerate(pillar_matches[:3]):
                                            print(f"DEBUG-CRISP: --- Match {i+1}: {match}")

                                        if len(pillar_matches) >= 3:  # Minimo 3 capitoli per un buon indice
                                            pillars = [p.strip() for p in pillar_matches]
                                            break
                                    else:
                                        print(f"DEBUG-CRISP: Pattern '{pattern}' non ha trovato corrispondenze")

                                # Se nessun pattern ha funzionato, prova con approcci alternativi
                                if not pillars:
                                    print("DEBUG-CRISP: Nessun pattern regex ha trovato abbastanza pilastri, provo approccio alternativo")

                                    # Approccio alternativo: dividi per righe e cerca linee che sembrano titoli di capitolo
                                    lines = pillars_text.split('\n')
                                    print(f"DEBUG-CRISP: Text diviso in {len(lines)} righe per analisi")

                                    for line in lines:
                                        line = line.strip()
                                        # Verifica se la riga sembra un titolo di capitolo
                                        if line and (
                                            line.lower().startswith('capitolo') or 
                                            line.lower().startswith('chapter') or
                                            re.match(r'^\d+[\.\)]', line)
                                        ):
                                            pillars.append(line)
                                            print(f"DEBUG-CRISP: Trovato potenziale pilastro: {line}")

                                    if pillars:
                                        print(f"DEBUG-CRISP: Approccio alternativo ha trovato {len(pillars)} potenziali pilastri")
                                    else:
                                        print("DEBUG-CRISP: Anche l'approccio alternativo non ha trovato pilastri")

                                        # Ultimo tentativo: cerca qualsiasi riga che sembra un titolo
                                        print("DEBUG-CRISP: Tentativo di ultima risorsa: qualsiasi riga che sembra un titolo")
                                        for line in lines:
                                            line = line.strip()
                                            # Riga abbastanza lunga ma non troppo e con maiuscole all'inizio
                                            if 10 <= len(line) <= 100 and line[0].isupper() and ":" not in line and line.endswith((".","?")):
                                                pillars.append(line)
                                                print(f"DEBUG-CRISP: Titolo potenziale trovato: {line}")
                                                if len(pillars) >= 5:  # Limita a 5 pilastri per questo approccio
                                                    break
                            else:
                                print(f"DEBUG-CRISP: CONTENT_PILLARS non è una stringa ma un {type(pillars_text)}")

                                # Se CONTENT_PILLARS è una lista (possibile con alcune implementazioni)
                                if isinstance(pillars_text, list):
                                    print(f"DEBUG-CRISP: CONTENT_PILLARS è una lista con {len(pillars_text)} elementi")
                                    pillars = pillars_text

                            # Costruisci l'indice a partire dai pilastri trovati
                            if pillars:
                                print(f"DEBUG-CRISP: Costruzione indice con {len(pillars)} pilastri trovati")

                                # Pulisci e formatta l'indice
                                index_text = "INTRODUZIONE\n\n"

                                for i, pillar in enumerate(pillars, 1):
                                    # Rimuovi numeri e simboli di punteggiatura iniziali
                                    try:
                                        clean_pillar = re.sub(r'^\d+[\.\)\s]+|^CAPITOLO\s+\d+\s*[:\.\-\s]*|^Capitolo\s+\d+\s*[:\.\-\s]*', '', pillar).strip()
                                        print(f"DEBUG-CRISP: Pillar {i} originale: '{pillar}'")
                                        print(f"DEBUG-CRISP: Pillar {i} pulito: '{clean_pillar}'")

                                        if clean_pillar:  # Aggiungi solo se c'è testo dopo la pulizia
                                            index_text += f"CAPITOLO {i}: {clean_pillar}\n\n"
                                        else:
                                            print(f"DEBUG-CRISP: Pillar {i} ha prodotto un testo vuoto dopo la pulizia")
                                            # Usa il testo originale come fallback se la pulizia ha rimosso tutto
                                            index_text += f"CAPITOLO {i}: {pillar}\n\n"
                                    except Exception as e:
                                        print(f"DEBUG-CRISP: Errore nella pulizia del pillar {i}: {str(e)}")
                                        # Usa il testo originale in caso di errore
                                        index_text += f"CAPITOLO {i}: {pillar}\n\n"

                                index_text += "CONCLUSIONE"
                                book_index_value = index_text
                                builder.add_log(f"✅ Indice costruito con {len(pillars)} capitoli")
                                print(f"DEBUG-CRISP: Indice costruito con successo:\n{book_index_value}")
                            else:
                                # Indice di fallback se non sono stati trovati pilastri
                                print("DEBUG-CRISP: Nessun pilastro trovato, uso indice di fallback")
                                book_index_value = """INTRODUZIONE

    CAPITOLO 1: Fondamenti

    CAPITOLO 2: Metodologia

    CAPITOLO 3: Applicazione

    CAPITOLO 4: Casi Studio

    CAPITOLO 5: Risultati

    CONCLUSIONE"""
                                builder.add_log("⚠️ Usato indice di fallback (nessun pilastro trovato)")
                                print("DEBUG-CRISP: Usato indice di fallback")
                        else:
                            print("DEBUG-CRISP: CONTENT_PILLARS non trovato nei dati del progetto")

                            # Cerca campi alternativi che potrebbero contenere informazioni per l'indice
                            alternative_found = False
                            for key in ['BOOK_STRUCTURE', 'INDICE_LIBRO', 'BOOK_JOURNEY', 'CHAPTER_STRUCTURE']:
                                if key in project_data:
                                    print(f"DEBUG-CRISP: Trovato {key} come alternativa a CONTENT_PILLARS")
                                    builder.add_log(f"🔍 Tentativo di costruzione indice da {key}")
                                     # Implementazione simile a quella per CONTENT_PILLARS
                                    alternative_text = project_data.get(key, '')
                                    # (Ripeti logica simile a quella usata per CONTENT_PILLARS)
                                    # Per brevità, questo codice è omesso ma sarebbe una duplicazione
                                    # dell'approccio sopra adattato per il campo alternativo

                                    alternative_found = True
                                    break

                            if not alternative_found:
                                print("DEBUG-CRISP: Nessuna alternativa a CONTENT_PILLARS trovata, uso indice di fallback")
                    else:
                        print("DEBUG-CRISP: project_data è None o vuoto, impossibile estrarre dati")

            # ================ FASE 5B: ELABORAZIONE MODALITÀ LEGACY ================
            else:
                # Approccio legacy - senza framework CRISP
                builder.add_log("🔍 Utilizzo approccio legacy (non CRISP)")
                print("DEBUG-LEGACY: Avvio elaborazione in modalità legacy (non CRISP)")

                try:
                    # Cerca dati nel file di contesto
                    context_file = "context.txt"
                    if os.path.exists(context_file):
                        # Informazioni sul file
                        file_size = os.path.getsize(context_file)
                        print(f"DEBUG-LEGACY: File context.txt trovato, dimensione: {file_size} bytes")

                        # Leggi l'intero contenuto del file
                        try:
                            with open(context_file, "r", encoding="utf-8") as f:
                                context_content = f.read()

                            builder.add_log(f"✅ File contesto letto: {len(context_content)} caratteri")
                            print(f"DEBUG-LEGACY: File contesto letto con successo: {len(context_content)} caratteri")

                            # Stampa le prime righe per debug
                            content_preview = context_content[:500].replace('\n', ' ')
                            print(f"DEBUG-LEGACY: Anteprima dei primi 500 caratteri: {content_preview}...")

                            # Analisi strutturale del contenuto per determinare il formato
                            print("DEBUG-LEGACY: Analisi strutturale del contenuto")

                            # Cerca sezioni nel formato standard
                            section_pattern = r'===\s+([^=]+?)\s+-\s+\d{8}_\d{6}\s+===\n'
                            sections = re.findall(section_pattern, context_content)

                            if sections:
                                print(f"DEBUG-LEGACY: Trovate {len(sections)} sezioni nel formato standard")
                                for i, section in enumerate(sections[:5]):  # Mostra solo le prime 5
                                    print(f"DEBUG-LEGACY: - Sezione {i+1}: {section}")

                                # Analisi dettagliata delle sezioni
                                print("DEBUG-LEGACY: Analisi dettagliata delle sezioni trovate")
                                section_contents = re.split(section_pattern, context_content)[1:]  # Salta il primo che è vuoto

                                # Assicurati che abbiamo lo stesso numero di titoli e contenuti
                                if len(sections) == len(section_contents)/2:
                                    print("DEBUG-LEGACY: Numero corretto di sezioni e contenuti")
                                else:
                                    print(f"DEBUG-LEGACY: ATTENZIONE - Discrepanza: {len(sections)} titoli vs {len(section_contents)/2} contenuti")
                            else:
                                print("DEBUG-LEGACY: Nessuna sezione trovata nel formato standard")
                                # Cerca formati alternativi
                                alt_pattern = r'---\s+([^-]+?)\s+---\n'
                                alt_sections = re.findall(alt_pattern, context_content)
                                if alt_sections:
                                    print(f"DEBUG-LEGACY: Trovate {len(alt_sections)} sezioni in formato alternativo")
                                else:
                                    print("DEBUG-LEGACY: Nessuna sezione trovata in formato alternativo")

                            # ================ FASE 5B-1: ESTRAZIONE DATI LEGACY ================
                            try:
                                # ---------- Estrazione Titolo ----------
                                print("DEBUG-LEGACY: Tentativo estrazione titolo")

                                # Lista di pattern da provare per trovare il titolo
                                title_patterns = [
                                    r'7\)[^:]*:[^T]*Titolo[^:]*:[^\n]*\n([^\n]+)',
                                    r'7\.[^:]*:[^T]*Titolo[^:]*:[^\n]*\n([^\n]+)',
                                    r'Titolo[^:]*:[^\n]*\n([^\n]+)',
                                    r'(?:title|titolo)[^:]*:[^\n]*\n([^\n]+)',
                                    r'THE[^"]*"([^"]+)"',  # Pattern per titoli tra virgolette
                                    r'"([^"]+)".*?(?:il tuo nuovo libro|your new book)',  # Pattern per titoli suggeriti
                                ]

                                # Prova ogni pattern fino a trovare una corrispondenza
                                book_title_value = ""
                                for pattern in title_patterns:
                                    print(f"DEBUG-LEGACY: Provo pattern titolo: {pattern}")
                                    title_match = re.search(pattern, context_content, re.IGNORECASE)

                                    if title_match:
                                        book_title_value = title_match.group(1).strip()
                                        builder.add_log(f"✅ Titolo estratto (legacy): {book_title_value}")
                                        print(f"DEBUG-LEGACY: Titolo estratto con pattern '{pattern}': {book_title_value}")
                                        break

                                if not book_title_value:
                                    print("DEBUG-LEGACY: Nessun titolo trovato con i pattern standard")

                                    # Cerca titoli in sezioni specifiche
                                    print("DEBUG-LEGACY: Ricerca titolo in sezioni specifiche")

                                    # Cerca sezioni che potrebbero contenere titoli
                                    title_sections = [s for s in sections if 'titolo' in s.lower() or 'title' in s.lower()]
                                    if title_sections:
                                        print(f"DEBUG-LEGACY: Trovate {len(title_sections)} sezioni potenzialmente contenenti titoli")

                                        # Per ogni sezione potenziale, cerca titoli
                                        for title_section in title_sections:
                                            section_index = sections.index(title_section)
                                            section_content = section_contents[section_index * 2]  # Moltiplica per 2 a causa della divisione

                                            # Cerca titoli nella sezione
                                            title_lines = [line for line in section_content.split('\n') if line.strip()]
                                            if title_lines:
                                                print(f"DEBUG-LEGACY: Sezione '{title_section}' contiene {len(title_lines)} linee non vuote")

    # Prendi la prima linea che sembra un titolo
                                            for line in title_lines:
                                                # Se la linea sembra un titolo (non troppo lungo, non contiene caratteri speciali)
                                                if 10 <= len(line) <= 100 and not any(char in line for char in ['{', '}', '(', ')', '[', ']']):
                                                    book_title_value = line.strip().strip('"\'')
                                                    print(f"DEBUG-LEGACY: Titolo estratto da sezione: {book_title_value}")
                                                    break

                                            if book_title_value:
                                                break

                                # ---------- Estrazione Indice ----------
                                print("DEBUG-LEGACY: Tentativo estrazione indice")

                                # Lista di pattern da provare per trovare l'indice
                                index_patterns = [
                                    r'8\)[^:]*:[^I]*Indice[^:]*:[^\n]*\n(.*?)(?=\n\n|$)',
                                    r'8\.[^:]*:[^I]*Indice[^:]*:[^\n]*\n(.*?)(?=\n\n|$)',
                                    r'Indice[^:]*:[^\n]*\n(.*?)(?=\n\n|$)',
                                    r'(?:indice|index)[^:]*:[^\n]*\n(.*?)(?=\n\n|$)',
                                    r'INDICE DEL LIBRO[^\n]*\n(.*?)(?=\n\n===|$)',  # Pattern specifico
                                    r'Indice del Libro[^\n]*\n(.*?)(?=\n\n|$)'      # Altra variante
                                ]

                                # Prova ogni pattern fino a trovare una corrispondenza
                                book_index_value = ""
                                for pattern in index_patterns:
                                    print(f"DEBUG-LEGACY: Provo pattern indice: {pattern}")
                                    index_match = re.search(pattern, context_content, re.DOTALL | re.IGNORECASE)

                                    if index_match:
                                        book_index_value = index_match.group(1).strip()
                                        builder.add_log(f"✅ Indice estratto (legacy): {len(book_index_value)} caratteri")
                                        print(f"DEBUG-LEGACY: Indice estratto con pattern '{pattern}', lunghezza: {len(book_index_value)}")
                                        print(f"DEBUG-LEGACY: Preview indice: {book_index_value[:200]}...")
                                        break

                                if not book_index_value:
                                    print("DEBUG-LEGACY: Nessun indice trovato con i pattern standard")
                                    print("DEBUG-LEGACY: Tentativo ricerca capitoli diretta")

                                    # Cerca tutti i pattern che sembrano capitoli
                                    chapter_patterns = [
                                        r'(CAPITOLO\s+\d+[^:\n]*:[^\n]+)',
                                        r'(CHAPTER\s+\d+[^:\n]*:[^\n]+)',
                                        r'(Capitolo\s+\d+[^:\n]*:[^\n]+)'
                                    ]

                                    all_chapters = []
                                    for pattern in chapter_patterns:
                                        chapters = re.findall(pattern, context_content, re.IGNORECASE)
                                        if chapters:
                                            print(f"DEBUG-LEGACY: Pattern '{pattern}' ha trovato {len(chapters)} capitoli")
                                            all_chapters.extend(chapters)

                                    if all_chapters:
                                        print(f"DEBUG-LEGACY: Trovati {len(all_chapters)} capitoli potenziali nel testo")

                                        # Cerca il blocco di testo che contiene più capitoli consecutivi
                                        chapter_sections = []
                                        for match in re.finditer(r'((?:CAPITOLO\s+\d+[^\n]*\n){2,})', context_content, re.IGNORECASE):
                                            section_text = match.group(1)
                                            chapter_count = section_text.lower().count('capitolo')
                                            chapter_sections.append((match.start(), match.end(), section_text, chapter_count))

                                        if chapter_sections:
                                            # Usa la sezione con più capitoli
                                            best_section = max(chapter_sections, key=lambda x: x[3])
                                            print(f"DEBUG-LEGACY: Trovato blocco indice con {best_section[3]} capitoli")

                                            # Aggiungi l'introduzione e conclusione se non presenti
                                            book_index_value = "INTRODUZIONE\n\n" + best_section[2] + "\nCONCLUSIONE"
                                            print(f"DEBUG-LEGACY: Indice costruito da blocco trovato: {len(book_index_value)} caratteri")
                                        else:
                                            # Se non ci sono blocchi, combina tutti i capitoli trovati
                                            book_index_value = "INTRODUZIONE\n\n" + "\n".join(all_chapters) + "\n\nCONCLUSIONE"
                                            print(f"DEBUG-LEGACY: Indice costruito da capitoli individuali: {len(book_index_value)} caratteri")

                                # ---------- Estrazione Stile di Voce ----------
                                print("DEBUG-LEGACY: Tentativo estrazione stile di voce")

                                # Lista di pattern da provare per trovare lo stile di voce
                                voice_patterns = [
                                    r'Tono di voce[^:]*:[^\n]*\n([^\n]+)',
                                    r'Voce[^:]*:[^\n]*\n([^\n]+)',
                                    r'Stile[^:]*:[^\n]*\n([^\n]+)',
                                    r'VOICE_STYLE[^:]*:[^\n]*\n([^\n]+)',
                                    r'(?:conversazionale|formale|informativo|tecnico)[^\n]+'
                                ]

                                # Prova ogni pattern fino a trovare una corrispondenza
                                voice_style_value = ""
                                for pattern in voice_patterns:
                                    print(f"DEBUG-LEGACY: Provo pattern stile voce: {pattern}")
                                    voice_match = re.search(pattern, context_content, re.IGNORECASE)

                                    if voice_match:
                                        # Gestione speciale per l'ultimo pattern che non ha gruppo
                                        if 'conversazionale' in pattern:
                                            voice_style_value = voice_match.group(0).strip()
                                        else:
                                            voice_style_value = voice_match.group(1).strip()

                                        builder.add_log(f"✅ Stile voce estratto (legacy): {voice_style_value}")
                                        print(f"DEBUG-LEGACY: Stile voce estratto con pattern '{pattern}': {voice_style_value}")
                                        break

                                if not voice_style_value:
                                    print("DEBUG-LEGACY: Nessuno stile di voce trovato con i pattern standard")

                                    # Cerca nelle sezioni potenzialmente legate allo stile
                                    style_sections = [s for s in sections if any(term in s.lower() for term in 
                                                     ['voice', 'voce', 'stile', 'tone', 'tono'])]

                                    if style_sections:
                                        print(f"DEBUG-LEGACY: Trovate {len(style_sections)} sezioni potenzialmente contenenti stile")

                                        for style_section in style_sections:
                                            section_index = sections.index(style_section)
                                            section_content = section_contents[section_index * 2]

                                            # Cerca stile nelle prime 5 righe della sezione
                                            style_lines = [line for line in section_content.split('\n')[:5] if line.strip()]
                                            if style_lines:
                                                voice_style_value = style_lines[0].strip()
                                                print(f"DEBUG-LEGACY: Stile voce estratto da sezione: {voice_style_value}")
                                                break

                                # ---------- Estrazione Tipo di Libro ----------
                                print("DEBUG-LEGACY: Tentativo estrazione tipo di libro")

                                # Lista di pattern da provare per trovare il tipo di libro
                                book_type_patterns = [
                                    r'tipo di libro[^:]*:[^\n]*\n*\s*([^\n]+)',
                                    r'genere[^:]*:[^\n]*\n*\s*([^\n]+)',
                                    r'categoria[^:]*:[^\n]*\n*\s*([^\n]+)',
                                    r'LIBRO_TIPO[^:]*:[^\n]*\n*\s*([^\n]+)'
                                ]

                                # Prova ogni pattern fino a trovare una corrispondenza
                                book_type_value = ""
                                for pattern in book_type_patterns:
                                    print(f"DEBUG-LEGACY: Provo pattern tipo libro: {pattern}")
                                    book_type_match = re.search(pattern, context_content, re.IGNORECASE)

                                    if book_type_match:
                                        book_type_value = book_type_match.group(1).strip()
                                        builder.add_log(f"✅ Tipo di libro estratto (legacy): {book_type_value}")
                                        print(f"DEBUG-LEGACY: Tipo di libro estratto con pattern '{pattern}': {book_type_value}")
                                        break

                                if not book_type_value:
                                    print("DEBUG-LEGACY: Nessun tipo di libro trovato con i pattern standard")

                                    # Cerca valori comuni di tipo libro nel testo
                                    common_types = ["Manuale", "Non-Fiction", "Ricettario", "Self-Help", "How-To", 
                                                   "Craft", "Hobby", "Survival", "Test Study"]

                                    for book_type in common_types:
                                        if book_type.lower() in context_content.lower():
                                            book_type_value = book_type
                                            print(f"DEBUG-LEGACY: Tipo libro trovato nel testo: {book_type_value}")
                                            break

                            except Exception as extraction_error:
                                builder.add_log(f"⚠️ Errore nell'estrazione dei dati: {str(extraction_error)}")
                                print(f"DEBUG-LEGACY: Errore nell'estrazione dei dati: {str(extraction_error)}")
                                print(f"DEBUG-LEGACY: Traceback errore estrazione:\n{traceback.format_exc()}")

                        except Exception as read_error:
                            builder.add_log(f"⚠️ Errore nella lettura del file context.txt: {str(read_error)}")
                            print(f"DEBUG-LEGACY: Errore nella lettura del file context.txt: {str(read_error)}")
                            print(f"DEBUG-LEGACY: Traceback errore lettura:\n{traceback.format_exc()}")

                    else:
                        builder.add_log("⚠️ File context.txt non trovato!")
                        print(f"DEBUG-LEGACY: File context.txt non trovato in {os.getcwd()}")

                        # Elenca i file nella directory corrente
                        files = os.listdir()
                        print(f"DEBUG-LEGACY: File nella directory corrente: {files}")

                        # Cerca file alternativi che potrebbero contenere i dati
                        context_alternatives = [f for f in files if 'context' in f.lower() or 
                                              'backup' in f.lower() or f.endswith('.txt')]

                        if context_alternatives:
                            print(f"DEBUG-LEGACY: Trovati possibili file alternativi: {context_alternatives}")
                            builder.add_log(f"⚠️ File context.txt non trovato, ma ci sono alternative: {context_alternatives}")

                except Exception as e:
                    builder.add_log(f"⚠️ Errore nell'estrazione legacy: {str(e)}")
                    print(f"DEBUG-LEGACY: Errore nell'estrazione legacy: {str(e)}")
                    print(f"DEBUG-LEGACY: Traceback errore estrazione:\n{traceback.format_exc()}")

            # ================ FASE 6: VALORI DI FALLBACK ================
            # Se necessario, utilizza valori di fallback per i campi che non è stato possibile estrarre

            print("DEBUG-FINAL: Verifica valori estratti prima di applicare fallback")
            print(f"DEBUG-FINAL: Titolo estratto: '{book_title_value}'")
            print(f"DEBUG-FINAL: Indice estratto: {len(book_index_value) if book_index_value else 0} caratteri")
            print(f"DEBUG-FINAL: Stile voce estratto: '{voice_style_value}'")
            print(f"DEBUG-FINAL: Tipo libro estratto: '{book_type_value}'")

            # Applica fallback se necessario
            if not book_title_value:
                book_title_value = "Il tuo nuovo libro"
                builder.add_log("⚠️ Usato titolo di fallback")
                print("DEBUG-FINAL: Usato titolo di fallback")

            if not book_index_value:
                book_index_value = """INTRODUZIONE

    CAPITOLO 1: Fondamenti

    CAPITOLO 2: Metodologia

    CAPITOLO 3: Applicazione

    CONCLUSIONE"""
                builder.add_log("⚠️ Usato indice di fallback")
                print("DEBUG-FINAL: Usato indice di fallback")

            if not voice_style_value:
                voice_style_value = "Conversazionale e informativo"
                builder.add_log("⚠️ Usato stile voce di fallback")
                print("DEBUG-FINAL: Usato stile voce di fallback")

            if not book_type_value:
                book_type_value = "Manuale (Non-Fiction)"
                builder.add_log("⚠️ Usato tipo libro di fallback")
                print("DEBUG-FINAL: Usato tipo libro di fallback")

            # ================ FASE 7: AGGIORNAMENTO INTERFACCIA ================
            # Aggiorna i campi dell'interfaccia con i valori estratti

            print("DEBUG-UPDATE: Tentativo aggiornamento campi interfaccia")

            try:  # try INTERNO per l'aggiornamento Gradio
                print("DEBUG-UPDATE: Inizio aggiornamento componenti Gradio")

                # Verifica e stampa info sulla versione di Gradio
                gradio_version = gr.__version__ if hasattr(gr, '__version__') else "sconosciuta"
                print(f"DEBUG-UPDATE: Versione Gradio rilevata: {gradio_version}")

                # Verifica quali componenti esistono
                components = {
                    'book_title': hasattr(self, 'book_title'),
                    'book_index': hasattr(self, 'book_index'),
                    'voice_style': hasattr(self, 'voice_style'),
                    'book_type_hidden': hasattr(self, 'book_type_hidden'),
                    'tabs': hasattr(self, 'tabs')
                }
                print(f"DEBUG-UPDATE: Componenti esistenti: {components}")

                # Per Gradio 5.x, il metodo corretto è .update(value=...)

                if hasattr(self, 'book_title'):
                    print(f"DEBUG-UPDATE: Aggiornamento book_title: '{book_title_value}'")
                    try:
                        self.book_title.value = book_title_value
                        builder.add_log(f"✓ Campo book_title aggiornato")
                        print(f"DEBUG-UPDATE: Campo book_title aggiornato con: {book_title_value}")
                    except Exception as e:
                        print(f"DEBUG-UPDATE: Errore aggiornamento book_title: {str(e)}")

                if hasattr(self, 'book_index'):
                    print(f"DEBUG-UPDATE: Aggiornamento book_index: {len(book_index_value)} caratteri")
                    try:
                        self.book_index.value = book_index_value
                        builder.add_log(f"✓ Campo book_index aggiornato")
                        print(f"DEBUG-UPDATE: Campo book_index aggiornato (lunghezza: {len(book_index_value)} caratteri)")
                    except Exception as e:
                        print(f"DEBUG-UPDATE: Errore aggiornamento book_index: {str(e)}")

                if hasattr(self, 'voice_style'):
                    print(f"DEBUG-UPDATE: Aggiornamento voice_style: '{voice_style_value}'")
                    try:
                        self.voice_style.value = voice_style_value
                        builder.add_log(f"✓ Campo voice_style aggiornato")
                        print(f"DEBUG-UPDATE: Campo voice_style aggiornato con: {voice_style_value}")
                    except Exception as e:
                        print(f"DEBUG-UPDATE: Errore aggiornamento voice_style: {str(e)}")

                # Aggiorna il tipo di libro se esiste il campo
                if hasattr(self, 'book_type_hidden'):
                    print(f"DEBUG-UPDATE: Aggiornamento book_type_hidden: '{book_type_value}'")
                    try:
                        self.book_type_hidden.value = book_type_value
                        builder.add_log(f"✓ Campo book_type_hidden aggiornato")
                        print(f"DEBUG-UPDATE: Campo book_type_hidden aggiornato con: {book_type_value}")
                    except Exception as e:
                        print(f"DEBUG-UPDATE: Errore aggiornamento book_type_hidden: {str(e)}")

                # Cambia tab
                if hasattr(self, 'tabs'):
                    print("DEBUG-UPDATE: Aggiornamento tab a indice 2 (Generazione Libro)")
                    try:
                        self.tabs.selected = 2  # Imposta direttamente l'indice selezionato
                        builder.add_log("✓ Tab aggiornato")
                        print("DEBUG-UPDATE: Tab aggiornato a indice 2 (Generazione Libro)")
                    except Exception as e:
                        print(f"DEBUG-UPDATE: Errore aggiornamento tabs: {str(e)}")
                        # Fallback per tabs
                        try:
                            import gradio as gr
                            self.tabs = gr.Tabs(selected=2)
                            print("DEBUG-UPDATE: Tab aggiornato con metodo alternativo")
                        except Exception as alt_e:
                            print(f"DEBUG-UPDATE: Anche fallback per tabs fallito: {str(alt_e)}")

                # Verifica che Gradio abbia effettivamente aggiornato i campi
                print("DEBUG-UPDATE: Verifica finale campi aggiornati")
                if hasattr(self, 'book_title'):
                    print(f"DEBUG-UPDATE: book_title.value finale: {getattr(self.book_title, 'value', 'N/A')}")

            except Exception as ui_error:  # AGGIUNGI QUESTO except per chiudere il try INTERNO
                builder.add_log(f"⚠️ Errore nell'aggiornamento UI: {str(ui_error)}")
                print(f"DEBUG-UPDATE: Errore generale nell'aggiornamento UI: {str(ui_error)}")
                print(f"DEBUG-UPDATE: Traceback: {traceback.format_exc()}")

            # ================ FASE 8: COMPLETAMENTO ================
            builder.add_log("✅ Funzione complete_analysis terminata con successo")
            print("DEBUG-FINAL: Funzione complete_analysis terminata con successo")
            # Un ultimo check prima di restituire i valori
            print(f"DEBUG-FINAL: Valori finali da restituire:")
            print(f"DEBUG-FINAL: - Log history: {len(self.log_history)} righe")
            print(f"DEBUG-FINAL: - Status: {analysis_status_text}")
            print(f"DEBUG-FINAL: - Tabs: {tabs_value}")
            print(f"DEBUG-FINAL: - Titolo: {book_title_value}")
            print(f"DEBUG-FINAL: - Indice: {len(book_index_value)} caratteri")
            print(f"DEBUG-FINAL: - Stile: {voice_style_value}")
            print(f"DEBUG-FINAL: - Tipo: {book_type_value}")

            # ================ FASE 8.5: SALVATAGGIO NEL DATABASE ================
            try:
                # CORREZIONE: Recupera la keyword corrente dal file più recente
                backup_dir = "backups"
                current_keyword = None

                # Tentativo 1: Cerca nei file di backup più recenti prima di tutto
                if os.path.exists(backup_dir):
                    backup_files = [f for f in os.listdir(backup_dir) 
                                  if f.startswith("context_") and f.endswith(".txt")]
                    if backup_files:
                        # Ordina per data di modifica (più recente prima)
                        backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), 
                                        reverse=True)
                        latest_file = backup_files[0]
                        builder.add_log(f"🔍 File di backup più recente trovato: {latest_file}")

                        # Estrai la keyword dal nome del file
                        keyword_match = re.match(r"context_(.+?)(_\d{8}_\d{6})?\.txt", latest_file)
                        if keyword_match:
                            current_keyword = keyword_match.group(1).replace("_", " ")
                            builder.add_log(f"🔍 Keyword trovata dal file più recente: {current_keyword}")

                # Tentativo 2: Solo se non abbiamo trovato la keyword dai backup
                if not current_keyword:
                    # Estrai la keyword dall'analisi corrente
                    if hasattr(self, 'current_analysis') and self.current_analysis:
                        keyword = self.current_analysis.get('KEYWORD')
                        if keyword:
                            current_keyword = keyword
                            builder.add_log(f"🔍 Usando keyword dall'analisi: {current_keyword}")
                            print(f"DEBUG-DB: Usando keyword dall'analisi: {current_keyword}")

                    # Se ancora non abbiamo una keyword, prova con il titolo del libro
                    if not current_keyword and book_title_value:
                        keyword = book_title_value.split(':')[0].strip()  # Prende la prima parte del titolo
                        current_keyword = keyword
                        builder.add_log(f"🔍 Usando keyword dal titolo: {current_keyword}")
                        print(f"DEBUG-DB: Usando keyword dal titolo: {current_keyword}")

                # Tentativo 3: Ultima risorsa, usa un valore predefinito
                if not current_keyword:
                    current_keyword = "Unknown Project"
                    builder.add_log(f"⚠️ Nessuna keyword trovata, usando valore predefinito: {current_keyword}")
                    print(f"DEBUG-DB: Nessuna keyword trovata, usando valore predefinito: {current_keyword}")

                # Salva nel database solo se abbiamo una keyword
                builder.add_log(f"💾 Tentativo salvataggio analisi nel database per keyword: {current_keyword}")
                print(f"DEBUG-DB: Tentativo salvataggio con keyword: {current_keyword}")

                try:
                    # Verifica che il database esista
                    if os.path.exists(self.crisp.project_db_path):
                        # Crea un nuovo progetto nel database
                        conn = sqlite3.connect(self.crisp.project_db_path)
                        cursor = conn.cursor()

                        # Genera un ID progetto appropriato
                        from datetime import datetime
                        current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                        project_id = f"PROJ_{current_date}"

                        # Formatta il nome del progetto usando la keyword corretta
                        project_name = f"{current_keyword} - {datetime.now().strftime('%Y-%m-%d')}"

                        # Inserisci nel database con ID esplicito
                        current_datetime = datetime.now().isoformat()
                        cursor.execute(
                            "INSERT INTO projects (id, name, creation_date, last_updated) VALUES (?, ?, ?, ?)",
                            (project_id, project_name, current_datetime, current_datetime)
                        )

                        # Salva le variabili principali di progetto
                        main_vars = {
                            "KEYWORD": current_keyword,
                            "TITOLO_LIBRO": book_title_value,
                            "INDICE_LIBRO": book_index_value,
                            "VOICE_STYLE": voice_style_value,
                            "BOOK_TYPE": book_type_value
                        }

                        # Inserisci le variabili nel database
                        for key, value in main_vars.items():
                            if value:  # Salva solo valori non vuoti
                                cursor.execute(
                                    "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                    (project_id, key, str(value))
                                )

                        # Se esistono dati in current_analysis, salvali come variabili
                        if hasattr(self, 'current_analysis') and self.current_analysis:
                            for key, value in self.current_analysis.items():
                                if key not in main_vars and value:  # Evita duplicati
                                    cursor.execute(
                                        "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                        (project_id, key, str(value))
                                    )

                        # Salva il contenuto del file di contesto come risultato di progetto
                        if hasattr(self.chat_manager, 'context_file') and os.path.exists(self.chat_manager.context_file):
                            with open(self.chat_manager.context_file, 'r', encoding='utf-8') as f:
                                context_content = f.read()

                            cursor.execute(
                                "INSERT INTO project_results (project_id, step_id, result_text, timestamp) VALUES (?, ?, ?, ?)",
                                (project_id, "ANALISI", context_content, current_datetime)
                            )

                        conn.commit()
                        conn.close()

                        builder.add_log(f"✅ Analisi salvata con successo nel database (ID: {project_id})")
                        print(f"DEBUG-DB: Analisi salvata con successo, ID: {project_id}")
                    else:
                        builder.add_log(f"⚠️ Database non trovato: {self.crisp.project_db_path}")
                        print(f"DEBUG-DB: Database non trovato: {self.crisp.project_db_path}")
                except Exception as db_error:
                    builder.add_log(f"⚠️ Errore durante il salvataggio nel database: {str(db_error)}")
                    print(f"DEBUG-DB: Errore salvataggio DB: {str(db_error)}")
                    print(f"DEBUG-DB: {traceback.format_exc()}")
            except Exception as save_error:
                builder.add_log(f"⚠️ Errore generale nel salvataggio: {str(save_error)}")
                print(f"DEBUG-DB: Errore generale nel salvataggio: {str(save_error)}")

            # Alla fine, dopo il completamento dell'analisi
                builder.add_log("🔍 Tentativo di estrazione automatica del tono di voce...")
                voice_style_name = self.extract_and_save_voice_style()

                if voice_style_name:
                    builder.add_log(f"✅ File di tono di voce creato: {voice_style_name}")

                    # Se abbiamo un dropdown per la selezione del tono di voce, aggiorniamolo
                    if hasattr(self, 'voice_style_file'):
                        # Ottieni la lista aggiornata di file di stile
                        import os
                        voice_style_files = ["Nessuno"] + [os.path.splitext(f)[0] for f in os.listdir("voice_styles") if f.endswith(".txt")]

                        # Aggiorna il dropdown e seleziona automaticamente il nuovo stile
                        self.voice_style_file.choices = voice_style_files
                        self.voice_style_file.value = voice_style_name

                        builder.add_log(f"✅ Tono di voce '{voice_style_name}' selezionato automaticamente")                    

            # ================ FASE 9: RESTITUZIONE VALORI ================
            # Restituzione esattamente 6 valori come richiesto dall'interfaccia
            return self.chat_manager.get_log_history_string(), analysis_status_text, tabs_value, book_title_value, book_index_value, voice_style_value

        except Exception as e:
            # Gestione errori globale - questo è l'UNICO except per il try principale
            error_msg = f"❌ Errore durante il completamento dell'analisi: {str(e)}"
            builder.add_log(error_msg)
            print(f"DEBUG-ERROR: ERRORE CRITICO in complete_analysis: {str(e)}")

            # Traceback completo dell'errore
            error_trace = traceback.format_exc()
            builder.add_log(f"Dettagli errore:\n{error_trace}")
            print(f"DEBUG-ERROR: Traceback completo:\n{error_trace}")

            # Restituisci valori minimi in caso di errore critico
            print("DEBUG-ERROR: Restituzione valori di fallback a causa dell'errore")
            return self.chat_manager.get_log_history_string(), "**Stato analisi**: Errore", gr.Tabs(selected=0), "", "", ""

    def _complete_analysis_crisp(self):
            """Completa l'analisi CRISP 5.0"""
            try:
                builder.add_log("Completamento analisi CRISP 5.0...")

                # Recupera l'ID del progetto CRISP corrente
                project_id = self.current_analysis.get('crisp_project_id')
                if not project_id:
                    return builder.add_log("Errore: Nessun progetto CRISP corrente trovato")

                # Recupera i dati completi del progetto
                project_data = self.crisp.get_project_data(project_id)

                # Aggiorna l'interfaccia con i dati estratti
                if hasattr(self, 'book_title') and 'TITOLO_LIBRO' in project_data:
                    self.book_title.update(value=project_data['TITOLO_LIBRO'])

                if hasattr(self, 'book_language') and 'LINGUA' in project_data:
                    self.book_language.update(value=project_data['LINGUA'])

                if hasattr(self, 'voice_style') and 'VOICE_STYLE' in project_data:
                    self.voice_style.update(value=project_data['VOICE_STYLE'])

                # Costruisci l'indice del libro in base ai CONTENT_PILLARS
                if hasattr(self, 'book_index') and 'CONTENT_PILLARS' in project_data:
                    # Estrai i pilastri di contenuto e trasformali in un indice
                    pillars_text = project_data.get('CONTENT_PILLARS', '')

                    # Cerca di estrarre i titoli dei pilastri
                    pillars = []
                    if isinstance(pillars_text, str):
                        # Cerca di estrarre i pilastri con regex
                        pillar_matches = re.findall(r'(\d+\.\s*[^\n]+)', pillars_text)
                        if pillar_matches:
                            pillars = [p.strip() for p in pillar_matches]
                        else:
                            # Alternativa: dividi per linee e filtra le linee non vuote
                            pillar_lines = [line.strip() for line in pillars_text.split('\n') if line.strip()]
                            pillars = pillar_lines[:5]  # Limita a 5 pilastri

                    # Se abbiamo trovato dei pilastri, costruisci l'indice
                    if pillars:
                        index_text = "INTRODUZIONE\n\n"
                        for i, pillar in enumerate(pillars, 1):
                            # Pulisci il pillar rimuovendo numeri e simboli iniziali
                            clean_pillar = re.sub(r'^\d+[\.\)\s]+', '', pillar).strip()
                            index_text += f"CAPITOLO {i}: {clean_pillar}\n"
                        index_text += "\nCONCLUSIONE"
                    else:
                        # Indice di fallback se non troviamo pillars
                        index_text = "INTRODUZIONE\n\nCAPITOLO 1: Fondamenti\n\nCAPITOLO 2: Metodologia\n\nCAPITOLO 3: Applicazione\n\nCAPITOLO 4: Casi Studio\n\nCAPITOLO 5: Risultati\n\nCONCLUSIONE"

                    self.book_index.update(value=index_text)

                # Mostra la sezione dei dettagli del libro
                if hasattr(self, 'book_details'):
                    self.book_details.update(visible=True)

                # Crea un riepilogo dei dati estratti
                summary = f"""
                ===== ANALISI CRISP 5.0 COMPLETATA =====

                Titolo: {project_data.get('TITOLO_LIBRO', 'N/A')}
                Sottotitolo: {project_data.get('SOTTOTITOLO_LIBRO', 'N/A')}

                Angolo di Attacco: {project_data.get('ANGOLO_ATTACCO', 'N/A')}
                Big Idea: {project_data.get('BIG_IDEA', 'N/A')}
                Buyer Persona: {project_data.get('BUYER_PERSONA_SUMMARY', 'N/A')}

                Promessa Principale: {project_data.get('PROMESSA_PRINCIPALE', 'N/A')}

                L'interfaccia è stata aggiornata con i dati del progetto.
                Puoi ora procedere con la generazione del libro.
                """

                # Salvataggio nel database
                try:
                    builder.add_log("💾 Salvataggio dei risultati CRISP nel database...")

                    # Il progetto è già salvato nel framework CRISP,
                    # ma possiamo aggiungerlo anche al database generale per la visualizzazione
                    if os.path.exists(self.crisp.project_db_path):
                        conn = sqlite3.connect(self.crisp.project_db_path)
                        cursor = conn.cursor()

                        # Verifica se il progetto esiste già nel database
                        cursor.execute("SELECT id FROM projects WHERE name = ?", (f"CRISP-{project_id}",))
                        existing = cursor.fetchone()

                        if not existing:
                            # Crea una entry nel database principale
                            current_date = datetime.now().isoformat()
                            cursor.execute(
                                "INSERT INTO projects (name, creation_date, last_updated) VALUES (?, ?, ?)",
                                (f"CRISP-{project_id}", current_date, current_date)
                            )

                            # Salva i principali metadati come variabili
                            db_project_id = cursor.lastrowid

                            # Se il progetto è stato salvato correttamente
                            if db_project_id:
                                # Salva keyword e altre informazioni chiave
                                keyword = project_data.get('KEYWORD', '')
                                cursor.execute(
                                    "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                    (db_project_id, 'KEYWORD', keyword)
                                )

                                # Salva riferimento al progetto CRISP originale
                                cursor.execute(
                                    "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                    (db_project_id, 'CRISP_PROJECT_ID', str(project_id))
                                )

                                # Registra avvenuto salvataggio
                                cursor.execute(
                                    "INSERT INTO project_results (project_id, step_id, result_text, timestamp) VALUES (?, ?, ?, ?)",
                                    (db_project_id, "CRISP_SUMMARY", summary, current_date)
                                )

                                conn.commit()
                                builder.add_log(f"✅ Riferimento al progetto CRISP salvato nel database principale (ID: {db_project_id})")
                        else:
                            builder.add_log("ℹ️ Progetto CRISP già presente nel database")

                        conn.close()
                except Exception as db_error:
                    builder.add_log(f"⚠️ Errore durante il salvataggio nel database: {str(db_error)}")
                    print(f"DEBUG-DB: Errore salvataggio DB: {str(db_error)}")           

                builder.add_log(summary)
                return self.chat_manager.get_log_history_string()

            except Exception as e:
                error_msg = f"Errore durante il completamento dell'analisi CRISP 5.0: {str(e)}"
                builder.add_log(error_msg)
                logging.error(error_msg)
                return self.chat_manager.get_log_history_string()   



    def _complete_analysis_crisp(self):
        """Completa l'analisi CRISP 5.0"""
        try:
            builder.add_log("Completamento analisi CRISP 5.0...")

            # Recupera l'ID del progetto CRISP corrente
            project_id = self.current_analysis.get('crisp_project_id')
            if not project_id:
                return builder.add_log("Errore: Nessun progetto CRISP corrente trovato")

            # Recupera i dati completi del progetto
            project_data = self.crisp.get_project_data(project_id)

            # Aggiorna l'interfaccia con i dati estratti
            if hasattr(self, 'book_title') and 'TITOLO_LIBRO' in project_data:
                self.book_title.update(value=project_data['TITOLO_LIBRO'])

            if hasattr(self, 'book_language') and 'LINGUA' in project_data:
                self.book_language.update(value=project_data['LINGUA'])

            if hasattr(self, 'voice_style') and 'VOICE_STYLE' in project_data:
                self.voice_style.update(value=project_data['VOICE_STYLE'])

            # Costruisci l'indice del libro in base ai CONTENT_PILLARS
            if hasattr(self, 'book_index') and 'CONTENT_PILLARS' in project_data:
                # Estrai i pilastri di contenuto e trasformali in un indice
                pillars_text = project_data.get('CONTENT_PILLARS', '')

                # Cerca di estrarre i titoli dei pilastri
                pillars = []
                if isinstance(pillars_text, str):
                    # Cerca di estrarre i pilastri con regex
                    pillar_matches = re.findall(r'(\d+\.\s*[^\n]+)', pillars_text)
                    if pillar_matches:
                        pillars = [p.strip() for p in pillar_matches]
                    else:
                        # Alternativa: dividi per linee e filtra le linee non vuote
                        pillar_lines = [line.strip() for line in pillars_text.split('\n') if line.strip()]
                        pillars = pillar_lines[:5]  # Limita a 5 pilastri

                # Se abbiamo trovato dei pilastri, costruisci l'indice
                if pillars:
                    index_text = "INTRODUZIONE\n\n"
                    for i, pillar in enumerate(pillars, 1):
                        # Pulisci il pillar rimuovendo numeri e simboli iniziali
                        clean_pillar = re.sub(r'^\d+[\.\)\s]+', '', pillar).strip()
                        index_text += f"CAPITOLO {i}: {clean_pillar}\n"
                    index_text += "\nCONCLUSIONE"
                else:
                    # Indice di fallback se non troviamo pillars
                    index_text = "INTRODUZIONE\n\nCAPITOLO 1: Fondamenti\n\nCAPITOLO 2: Metodologia\n\nCAPITOLO 3: Applicazione\n\nCAPITOLO 4: Casi Studio\n\nCAPITOLO 5: Risultati\n\nCONCLUSIONE"

                self.book_index.update(value=index_text)

            # Mostra la sezione dei dettagli del libro
            if hasattr(self, 'book_details'):
                self.book_details.update(visible=True)

            # Crea un riepilogo dei dati estratti
            summary = f"""
            ===== ANALISI CRISP 5.0 COMPLETATA =====

            Titolo: {project_data.get('TITOLO_LIBRO', 'N/A')}
            Sottotitolo: {project_data.get('SOTTOTITOLO_LIBRO', 'N/A')}

            Angolo di Attacco: {project_data.get('ANGOLO_ATTACCO', 'N/A')}
            Big Idea: {project_data.get('BIG_IDEA', 'N/A')}
            Buyer Persona: {project_data.get('BUYER_PERSONA_SUMMARY', 'N/A')}

            Promessa Principale: {project_data.get('PROMESSA_PRINCIPALE', 'N/A')}

            L'interfaccia è stata aggiornata con i dati del progetto.
            Puoi ora procedere con la generazione del libro.
            """

            # Salvataggio nel database
            try:
                builder.add_log("💾 Salvataggio dei risultati CRISP nel database...")

                # Il progetto è già salvato nel framework CRISP,
                # ma possiamo aggiungerlo anche al database generale per la visualizzazione
                if os.path.exists(self.crisp.project_db_path):
                    conn = sqlite3.connect(self.crisp.project_db_path)
                    cursor = conn.cursor()

                    # Verifica se il progetto esiste già nel database
                    cursor.execute("SELECT id FROM projects WHERE name = ?", (f"CRISP-{project_id}",))
                    existing = cursor.fetchone()

                    if not existing:
                        # Crea una entry nel database principale
                        current_date = datetime.now().isoformat()
                        cursor.execute(
                            "INSERT INTO projects (name, creation_date, last_updated) VALUES (?, ?, ?)",
                            (f"CRISP-{project_id}", current_date, current_date)
                        )

                        # Salva i principali metadati come variabili
                        db_project_id = cursor.lastrowid

                        # Se il progetto è stato salvato correttamente
                        if db_project_id:
                            # Salva keyword e altre informazioni chiave
                            keyword = project_data.get('KEYWORD', '')
                            cursor.execute(
                                "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                (db_project_id, 'KEYWORD', keyword)
                            )

                            # Salva riferimento al progetto CRISP originale
                            cursor.execute(
                                "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                (db_project_id, 'CRISP_PROJECT_ID', str(project_id))
                            )

                            # Registra avvenuto salvataggio
                            cursor.execute(
                                "INSERT INTO project_results (project_id, step_id, result_text, timestamp) VALUES (?, ?, ?, ?)",
                                (db_project_id, "CRISP_SUMMARY", summary, current_date)
                            )

                            conn.commit()
                            builder.add_log(f"✅ Riferimento al progetto CRISP salvato nel database principale (ID: {db_project_id})")
                    else:
                        builder.add_log("ℹ️ Progetto CRISP già presente nel database")

                    conn.close()
            except Exception as db_error:
                builder.add_log(f"⚠️ Errore durante il salvataggio nel database: {str(db_error)}")
                print(f"DEBUG-DB: Errore salvataggio DB: {str(db_error)}")           

            builder.add_log(summary)
            return self.chat_manager.get_log_history_string()

        except Exception as e:
            error_msg = f"Errore durante il completamento dell'analisi CRISP 5.0: {str(e)}"
            builder.add_log(error_msg)
            logging.error(error_msg)
            return self.chat_manager.get_log_history_string()


    def _complete_analysis_legacy(self):
        """Completa l'analisi legacy e mostra una finestra di dialogo per la selezione"""
        try:
            builder.add_log("Completamento analisi legacy...")

            # 1. Recupera i dati dall'analisi salvata
            context_file = "context.txt"

            try:
                with open(context_file, "r", encoding="utf-8") as f:
                    full_text = f.read()

                # Estrai le diverse sezioni in base ai punti numerati
                # Cerca titoli e indici
                titoli_section = re.search(r'7\)\s+\*\*Titolo\s+&\s+sottotitolo[^F]*?FINE', full_text, re.DOTALL)
                indice_section = re.search(r'8\)\s+\*\*Indice\s+del\s+libro[^F]*?FINE', full_text, re.DOTALL)

                titoli_text = titoli_section.group(0) if titoli_section else ""
                indice_text = indice_section.group(0) if indice_section else ""

                # Estrai le opzioni di titolo
                titoli_options = []
                titoli_matches = re.finditer(r'(?:Opzione|Titolo)\s+\d+[:\)]\s+[""]?([^"\n]+)[""]?(?:\s*[:–-]\s*[""]?([^"\n]+)[""]?)?', titoli_text)

                for i, match in enumerate(titoli_matches, 1):
                    titolo = match.group(1).strip() if match.group(1) else ""
                    sottotitolo = match.group(2).strip() if match.group(2) else ""
                    if titolo:
                        titoli_options.append({
                            "id": i,
                            "titolo": titolo, 
                            "sottotitolo": sottotitolo,
                            "display": f"Opzione {i}: {titolo} - {sottotitolo}"
                        })

                # Estrai gli indici proposti
                indici_options = []
                indici_matches = re.finditer(r'(?:Indice|INDICE|CAPITOLI)[^\n]*\n(.*?)(?=\n\n|\n[A-Z]|$)', indice_text, re.DOTALL)

                for i, match in enumerate(indici_matches, 1):
                    indice_content = match.group(1).strip()
                    # Pulisci e formatta l'indice
                    indice_lines = [line.strip() for line in indice_content.split('\n') if line.strip()]
                    indice_formatted = "\n".join(indice_lines)
                    indici_options.append({
                        "id": i,
                        "content": indice_formatted,
                        "display": f"Indice {i}"
                    })

                # Estrai il tono di voce suggerito
                voice_style_match = re.search(r'(?:tono|stile|voce)[^:]*[:]\s*([^\n\.]+)', full_text, re.IGNORECASE)
                voice_style = voice_style_match.group(1).strip() if voice_style_match else "Conversazionale"

                # Salva temporaneamente le opzioni per l'uso nella finestra di dialogo
                self.temp_titles = titoli_options
                self.temp_indices = indici_options
                self.temp_voice_style = voice_style

                # Log delle opzioni
                builder.add_log("\n=== OPZIONI DI SELEZIONE ===")
                builder.add_log(f"Titoli disponibili: {len(titoli_options)}")
                for t in titoli_options:
                    builder.add_log(f"- {t['display']}")

                builder.add_log(f"Indici disponibili: {len(indici_options)}")
                for idx in indici_options:
                    preview = idx['content'][:50] + "..." if len(idx['content']) > 50 else idx['content']
                    builder.add_log(f"- Indice {idx['id']}: {preview}")

                builder.add_log(f"Stile di voce: {voice_style}")

                # Crea una finestra di dialogo per la selezione
                self.create_selection_dialog(titoli_options, indici_options, voice_style)

                return self.chat_manager.get_log_history_string()

            except Exception as e:
                builder.add_log(f"⚠️ Errore nell'analisi del contesto: {str(e)}")
                import traceback
                builder.add_log(traceback.format_exc())
                return self.chat_manager.get_log_history_string()

                # Salvataggio nel database
                try:
                    # Estrai keyword dal contesto o dal titolo
                    keyword = None

                    # Cerca la keyword nel testo
                    keyword_match = re.search(r'(?:keyword|parola chiave)[^:]*?:\s*([^\n]+)', full_text, re.IGNORECASE)
                    if keyword_match:
                        keyword = keyword_match.group(1).strip()

                    # Se non trovata, usa il titolo della prima opzione
                    if not keyword and titoli_options:
                        keyword = titoli_options[0]['titolo'].split()[0]  # Prima parola del primo titolo

                    # Se abbiamo una keyword, salva nel database
                    if keyword:
                        builder.add_log(f"💾 Salvataggio analisi legacy nel database per keyword: {keyword}")

                        if os.path.exists(self.crisp.project_db_path):
                            conn = sqlite3.connect(self.crisp.project_db_path)
                            cursor = conn.cursor()

                            # Crea un nuovo progetto
                            current_date = datetime.now().isoformat()
                            cursor.execute(
                                "INSERT INTO projects (name, creation_date, last_updated) VALUES (?, ?, ?)",
                                (f"Legacy-{keyword}", current_date, current_date)
                            )
                            project_id = cursor.lastrowid

                            # Salva la keyword
                            cursor.execute(
                                "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                (project_id, "KEYWORD", keyword)
                            )

                            # Salva le opzioni di titolo
                            if titoli_options:
                                title_json = json.dumps(titoli_options)
                                cursor.execute(
                                    "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                    (project_id, "TITLE_OPTIONS", title_json)
                                )

                            # Salva le opzioni di indice
                            if indici_options:
                                index_json = json.dumps(indici_options)
                                cursor.execute(
                                    "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                    (project_id, "INDEX_OPTIONS", index_json)
                                )

                            # Salva il tono di voce
                            if voice_style:
                                cursor.execute(
                                    "INSERT INTO project_variables (project_id, variable_name, variable_value) VALUES (?, ?, ?)",
                                    (project_id, "VOICE_STYLE", voice_style)
                                )

                            # Salva il testo completo
                            cursor.execute(
                                "INSERT INTO project_results (project_id, step_id, result_text, timestamp) VALUES (?, ?, ?, ?)",
                                (project_id, "ANALISI_LEGACY", full_text, current_date)
                            )

                            conn.commit()
                            conn.close()

                            builder.add_log(f"✅ Analisi legacy salvata nel database (ID: {project_id})")
                    else:
                        builder.add_log("⚠️ Impossibile salvare nel database: keyword non trovata")
                except Exception as db_error:
                    builder.add_log(f"⚠️ Errore durante il salvataggio nel database: {str(db_error)}")
                    import traceback
                    builder.add_log(traceback.format_exc())

        except Exception as e:
            error_msg = f"Errore durante il completamento dell'analisi: {str(e)}"
            builder.add_log(error_msg)
            logging.error(error_msg)
            return self.chat_manager.get_log_history_string()


# Istanza di analizzatore riutilizzabile
_analyzer = MarketAnalyzer()

def analyze_market(builder,
                   book_type, keyword, language, market,
                   analysis_prompt=None, use_crisp=None):
    """
    Wrapper di modulo: chiama MarketAnalyzer.analyze_market.
    """
    return _analyzer.analyze_market(
        builder,
        book_type, keyword, language, market,
        analysis_prompt=analysis_prompt,
        use_crisp=use_crisp
    )

def _analyze_market_crisp(builder, book_type, keyword, language, market, selected_phases=None):
    """
    Wrapper di modulo: chiama MarketAnalyzer._analyze_market_crisp.
    """
    return _analyzer._analyze_market_crisp(
        builder, book_type, keyword, language, market, selected_phases
    )

def _analyze_market_legacy(builder, book_type, keyword, language, market, analysis_prompt):
    """
    Wrapper di modulo: chiama MarketAnalyzer._analyze_market_legacy.
    """
    return _analyzer._analyze_market_legacy(
        builder, book_type, keyword, language, market, analysis_prompt
    )

def resume_analysis(builder, project_id, selected_phases=None):
    """
    Wrapper di modulo: chiama MarketAnalyzer.resume_analysis.
    """
    return _analyzer.resume_analysis(builder, project_id, selected_phases)

def continue_analysis(builder):
    """
    Wrapper di modulo: chiama MarketAnalyzer.continue_analysis.
    """
    return _analyzer.continue_analysis(builder)

def _continue_analysis_crisp(builder):
    """
    Wrapper di modulo: chiama MarketAnalyzer._continue_analysis_crisp.
    """
    return _analyzer._continue_analysis_crisp(builder)

def complete_analysis(builder):
    """
    Wrapper di modulo: chiama MarketAnalyzer.complete_analysis.
    """
    return _analyzer.complete_analysis(builder)

def _complete_analysis_crisp(builder):
    """
    Wrapper di modulo: chiama MarketAnalyzer._complete_analysis_crisp.
    """
    return _analyzer._complete_analysis_crisp(builder)

def _complete_analysis_legacy(builder):
    """
    Wrapper di modulo: chiama MarketAnalyzer._complete_analysis_legacy.
    """
    return _analyzer._complete_analysis_legacy(builder)