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
if getattr(self, 'analysis_type_radio', None) is not None:
    builder.add_log(f"DEBUG: analysis_type_radio esiste: valore = {self.analysis_type_radio.value}")
else:
    builder.add_log("DEBUG: analysis_type_radio non impostato (None)")
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
            if hasattr(builder, 'results_display'):
                # Modalità UI: aggiorna l'HTML e attendi la risposta asincrona
                if hasattr(builder.results_display, 'update'):
                    builder.results_display.update(value=warning_html)
                # Qui dovresti implementare un sistema di callback per gestire la risposta
                # Per ora restituisci solo il log
                return builder.chat_manager.get_log_history_string()
            else:
                # Modalità console
                choice = input("Inserisci il numero della tua scelta (1/2/3): ")

                if choice == "2":
                    # Carica i dettagli del progetto esistente
                    details = self.load_project_details(project_id)
                    buider.add_log(details)
                    return builder.chat_manager.get_log_history_string()

                elif choice == "3":
                    # Ripristina l'analisi esistente
                    return self.ripristina_analisi_da_database(project_id)

                # Se choice è "1" o altro, continua normalmente con una nuova analisi
        except Exception as input_error:
            builder.add_log(f"Errore nell'interazione con l'utente: {str(input_error)}")
            builder.add_log("Procedo con una nuova analisi...")
            # Continua con l'analisi normalmente

    # Da qui in poi è il codice originale per l'analisi

    # 1) Verifico login e driver
    from ai_interfaces.browser_manager import get_connection_status
    if not get_connection_status() or not builder.driver:
        return builder.add_log("Errore: Devi prima connetterti!")

    # 2) Avvio analisi
    builder.add_log(f"Avvio analisi di mercato per: {keyword}")

    # Inizializza/reimposta lo stato delle domande
    if not hasattr(self, 'question_status'):
        self.question_status = {}
    else:
        self.question_status.clear()

    # 3) Decido se usare CRISP o il metodo legacy in base al radio button in builder
    # Leggo direttamente builder.analysis_type_radio.value, se esiste e non è None
    if hasattr(builder, 'analysis_type_radio') and builder.analysis_type_radio is not None:
        analysis_type = builder.analysis_type_radio.value  # dovrebbe restituire "CRISP" o "Legacy"
        builder.add_log(f"DEBUG: Usando tipo di analisi dal radio: {analysis_type}")
    else:
        # Se non c’è ancora un radio impostato, uso use_crisp se è stato passato,
        # altrimenti default a CRISP
        if use_crisp is not None:
            analysis_type = "CRISP" if use_crisp else "Legacy"
            builder.add_log(f"DEBUG: use_crisp passato: {use_crisp} → analysis_type = {analysis_type}")
        else:
            analysis_type = "CRISP"
            builder.add_log(f"DEBUG: Fallback analysis_type = {analysis_type}")

    # Ora imposto use_crisp_for_this_run
    use_crisp_for_this_run = (analysis_type == "CRISP")
    builder.add_log(f"ℹ️ Modalità analisi selezionata: {analysis_type} (use_crisp_for_this_run = {use_crisp_for_this_run})")

    import re
    selected_phases = []

    if use_crisp_for_this_run:
        builder.add_log("DEBUG – Leggo fasi CRISP da builder.crisp_phase_checkboxes")
        try:
            for v in builder.crisp_phase_checkboxes.value:
                m = re.match(r'([A-Z]+-[0-9A-Z]+):', v)
                if m:
                    selected_phases.append(m.group(1))
            builder.add_log(f"🔍 Fasi CRISP selezionate: {', '.join(selected_phases)}")
        except Exception as ex:
            builder.add_log(f"⚠️ Errore lettura fasi CRISP: {ex}")
    else:
        builder.add_log("DEBUG – Leggo fasi Legacy da builder.legacy_phase_checkboxes")
        try:
            for v in builder.legacy_phase_checkboxes.value:
                m = re.search(r'-(\d+)', v)
                if m:
                    selected_phases.append(int(m.group(1)))
            builder.add_log(f"🔍 Fasi Legacy selezionate: {', '.join(str(p) for p in selected_phases)}")
        except Exception as ex:
            builder.add_log(f"⚠️ Errore lettura fasi Legacy: {ex}")

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
                builder.chat_manager.save_response(
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
                html_results = builder.format_analysis_results_html(keyword, market, book_type, language, context)



                # Aggiorna il display dei risultati
                # Usa assegnazione diretta invece di update
                if hasattr(builder.results_display, 'update'):
                    builder.results_display.update(value=html_results)
                else:
                    builder.results_display.value = html_results
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
                builder.chat_manager.save_response(
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
            builder.analysis_status.update(value="**Stato analisi**: Completata ✅")

        # Verifica che builder.results_display e builder.analysis_status non siano lo stesso oggetto
        if hasattr(self, 'results_display') and hasattr(self, 'analysis_status'):
            same_object = id(builder.results_display) == id(builder.analysis_status)
            if same_object:
                builder.add_log("⚠️ results_display e analysis_status sono lo stesso oggetto, evito di caricare i risultati per prevenire sovrascritture")
            else:
                # Carica i risultati solo se sono oggetti diversi
                builder.load_analysis_results()
        else:
            # Se uno dei due non esiste, procedi normalmente
            builder.load_analysis_results()

        builder.add_log("📌 Analisi parziale completata. Premi '✅ Completa Analisi' per salvare nel database.")

        return result

except Exception as e:
    error_msg = f"Errore durante l'analisi: {str(e)}"
    builder.add_log(error_msg)
    logging.error(error_msg)
    return builder.chat_manager.get_log_history_string()
