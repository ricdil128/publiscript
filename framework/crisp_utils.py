"""
Utility per il framework CRISP.
Fornisce funzioni generiche per la gestione dei prompt e l'elaborazione dei risultati.
"""
import re
import json
import logging
from pathlib import Path
from docx import Document
from datetime import datetime

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("crisp_utils")

def load_docx_content(file_path):
    """
    Carica il contenuto di un file DOCX o TXT.
    Prova diverse codifiche per i file TXT.
    
    Args:
        file_path: Percorso del file
        
    Returns:
        str: Contenuto testuale del documento
    """
    try:
        file_path = Path(file_path)
        
        # Se è un file .txt, caricalo provando diverse codifiche
        if file_path.suffix.lower() == '.txt':
            # Lista delle codifiche da provare
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            # Prova ciascuna codifica fino a trovarne una che funziona
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"File {file_path} aperto con codifica {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            # Se nessuna codifica ha funzionato, solleva un'eccezione
            if content is None:
                raise ValueError(f"Impossibile decodificare il file con le codifiche: {encodings}")
                
            # Aggiungi le sezioni necessarie se non sono presenti
            if "------ METADATA ------" not in content:
                # Determina le variabili in base al nome file
                file_stem = file_path.stem
                variables = ["KEYWORD", "MERCATO", "LINGUA"]
                
                if "Buyer" in file_stem:
                    variables.extend(["COMPETITOR1", "COMPETITOR2", "COMPETITOR3"])
                if "Angolo" in file_stem:
                    variables.append("BUYER_PERSONA_SUMMARY")
                if "Titolo" in file_stem:
                    variables.extend(["ANGOLO_ATTACCO", "BUYER_PERSONA_SUMMARY", "PROMESSA_PRINCIPALE"])
                
                # Crea la struttura formattata
                formatted_content = f"""
------ METADATA ------
Title: {file_stem}
Version: 1.0
------ END METADATA ------

------ VARIABLES ------
{chr(10).join(variables)}
------ END VARIABLES ------

------ PROMPT ------
{content}
------ END PROMPT ------
"""
                return formatted_content
            
            return content
        
        # Altrimenti, carica il file DOCX
        doc = Document(file_path)
        content = "\n".join([p.text for p in doc.paragraphs])
        
        # Aggiungi le sezioni necessarie se non sono presenti
        if "------ METADATA ------" not in content:
            file_stem = file_path.stem
            variables = ["KEYWORD", "MERCATO", "LINGUA"]
            
            formatted_content = f"""
------ METADATA ------
Title: {file_stem}
Version: 1.0
------ END METADATA ------

------ VARIABLES ------
{chr(10).join(variables)}
------ END VARIABLES ------

------ PROMPT ------
{content}
------ END PROMPT ------
"""
            return formatted_content
        
        return content
    except Exception as e:
        logger.error(f"Errore caricamento file {file_path}: {str(e)}")
        raise ValueError(f"Impossibile caricare il file: {str(e)}")

def extract_section(text, section_name):
    """
    Estrae una sezione specifica da un testo delimitato.
    Versione migliorata che supporta vari formati e gestisce ID errati.
    
    Args:
        text: Testo completo
        section_name: Nome della sezione da estrarre
        
    Returns:
        str: Contenuto della sezione
    """
    # Prova prima con il pattern originale
    pattern = f"------ {section_name} ------(.+?)------ END {section_name} ------"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        # Verifica che il contenuto estratto non contenga metadati con ID errato
        if section_name == "PROMPT" and "----- METADATA -----" in content and "ID:" in content:
            # Estrai il PROMPT all'interno del contenuto errato
            inner_match = re.search(r'------ PROMPT ------(.+?)------ END PROMPT ------', content, re.DOTALL)
            if inner_match:
                actual_content = inner_match.group(1).strip()
                print(f"DEBUG - Corretto contenuto con ID errato: {len(actual_content)} caratteri")
                return actual_content
            else:
                print(f"DEBUG - Contenuto PROMPT contiene metadati errati ma impossibile estrarre il prompt interno")
        else:
            print(f"DEBUG - Sezione {section_name} trovata con pattern originale")
            return content
    
    # Se non funziona, prova con pattern più flessibile (5 trattini)
    alt_pattern = f"----- {section_name} -----(.+?)----- END {section_name} ------"
    alt_match = re.search(alt_pattern, text, re.DOTALL)
    if alt_match:
        content = alt_match.group(1).strip()
        # Verifica che il contenuto estratto non contenga metadati con ID errato
        if section_name == "PROMPT" and "----- METADATA -----" in content and "ID:" in content:
            # Estrai il PROMPT all'interno del contenuto errato
            inner_match = re.search(r'------ PROMPT ------(.+?)------ END PROMPT ------', content, re.DOTALL)
            if inner_match:
                actual_content = inner_match.group(1).strip()
                print(f"DEBUG - Corretto contenuto con ID errato (alt): {len(actual_content)} caratteri")
                return actual_content
            else:
                print(f"DEBUG - Contenuto PROMPT contiene metadati errati ma impossibile estrarre il prompt interno (alt)")
        else:
            print(f"DEBUG - Sezione {section_name} trovata con pattern alternativo")
            return content
    
    # Pattern ancora più flessibile che accetta spazi variabili
    flex_pattern = f"[-]{3,7}\\s*{section_name}\\s*[-]{3,7}(.+?)[-]{3,7}\\s*END\\s*{section_name}\\s*[-]{3,7}"
    flex_match = re.search(flex_pattern, text, re.DOTALL)
    if flex_match:
        content = flex_match.group(1).strip()
        # Verifica che il contenuto estratto non contenga metadati con ID errato
        if section_name == "PROMPT" and "----- METADATA -----" in content and "ID:" in content:
            # Estrai il PROMPT all'interno del contenuto errato
            inner_match = re.search(r'------ PROMPT ------(.+?)------ END PROMPT ------', content, re.DOTALL)
            if inner_match:
                actual_content = inner_match.group(1).strip()
                print(f"DEBUG - Corretto contenuto con ID errato (flex): {len(actual_content)} caratteri")
                return actual_content
            else:
                print(f"DEBUG - Contenuto PROMPT contiene metadati errati ma impossibile estrarre il prompt interno (flex)")
        else:
            print(f"DEBUG - Sezione {section_name} trovata con pattern flessibile")
            return content
    
    # Tentativo diretto se si tratta di sezione PROMPT
    if section_name == "PROMPT":
        # Cerca il prompt nella parte finale del file
        if "------ PROMPT ------" in text:
            print("DEBUG - Tentativo di estrazione diretta di PROMPT")
            parts = text.split("------ PROMPT ------")
            if len(parts) > 1:
                last_part = parts[-1]
                if "------ END PROMPT ------" in last_part:
                    direct_content = last_part.split("------ END PROMPT ------")[0].strip()
                    # Verifica che non ci siano metadati
                    if not "----- METADATA -----" in direct_content:
                        print(f"DEBUG - Estratto PROMPT direttamente: {len(direct_content)} caratteri")
                        return direct_content
    
    print(f"DEBUG - Impossibile estrarre la sezione {section_name}")
    return ""

def replace_variables(text, variables):
    """
    Sostituisce le variabili nel testo con i valori forniti.
    Supporta sia {VARIABLE} che ${VARIABLE}.
    Case-insensitive per una maggiore flessibilità.
    
    Args:
        text: Testo con variabili
        variables: Dizionario delle variabili {nome: valore}
        
    Returns:
        str: Testo con variabili sostituite
    """
    result = text
    
    # Crea un dizionario case-insensitive
    case_insensitive_vars = {}
    for key, value in variables.items():
        case_insensitive_vars[key.upper()] = value
        case_insensitive_vars[key.lower()] = value
    
    # Sostituisci variabili nel formato {VARIABLE}
    for var_name, var_value in case_insensitive_vars.items():
        placeholder1 = "{" + var_name + "}"
        placeholder2 = "${" + var_name + "}"
        
        if placeholder1 in result:
            result = result.replace(placeholder1, str(var_value))
        
        # Prova anche la versione con $
        if placeholder2 in result:
            result = result.replace(placeholder2, str(var_value))
    
    # Verifica se sono rimaste variabili non sostituite
    remaining_vars = re.findall(r'\{([A-Za-z_]+)\}', result)
    if remaining_vars:
        logger.warning(f"Variabili non sostituite: {remaining_vars}")
    
    return result

def sanitize_filename(text):
    """
    Pulisce un testo per renderlo utilizzabile come nome file.
    
    Args:
        text: Testo da sanitizzare
        
    Returns:
        str: Testo sanitizzato
    """
    # Rimuovi caratteri non validi per i nomi file
    cleaned = re.sub(r'[\\/*?:"<>|]', "", text)
    # Sostituisci spazi con underscore
    cleaned = cleaned.replace(" ", "_")
    # Limita la lunghezza
    if len(cleaned) > 50:
        cleaned = cleaned[:47] + "..."
    return cleaned

def create_timestamp():
    """
    Crea un timestamp formattato.
    
    Returns:
        str: Timestamp formattato (YYYYMMDD_HHMMSS)
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_result(result, project_id, step_id, output_dir="output"):
    """
    Salva il risultato di uno step in un file.
    
    Args:
        result: Testo del risultato
        project_id: ID del progetto
        step_id: ID dello step
        output_dir: Directory di output
        
    Returns:
        str: Percorso del file salvato
    """
    # Crea la directory se non esiste
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Crea il nome file
    timestamp = create_timestamp()
    filename = f"{project_id}_{step_id}_{timestamp}.txt"
    file_path = output_path / filename
    
    # Salva il risultato
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    
    logger.info(f"Risultato salvato in {file_path}")
    return str(file_path)

def find_prompt_file(prompt_id, prompt_dir="prompt_crisp"):
    """
    Trova il file corrispondente a un prompt ID.
    Supporta sia file .docx che .txt nella directory principale.
    
    Args:
        prompt_id: ID del prompt (es. "CM-1", "CS-2")
        prompt_dir: Directory dei prompt
        
    Returns:
        Path: Percorso del file
    """
    prompt_dir_path = Path(prompt_dir)
    
    # Cerca direttamente nella directory principale
    # Prima cerca i file con nome esatto
    exact_txt = prompt_dir_path / f"{prompt_id}.txt"
    if exact_txt.exists():
        logger.info(f"Trovato file prompt {prompt_id}: {exact_txt}")
        return exact_txt
    
    exact_docx = prompt_dir_path / f"{prompt_id}.docx"
    if exact_docx.exists():
        logger.info(f"Trovato file prompt {prompt_id}: {exact_docx}")
        return exact_docx
    
    # Supporto per il nuovo formato con trattino
    if "-" in prompt_id:
        base_id, sub_id = prompt_id.split("-", 1)
        
        # Cerca con formato CM-1.txt o CS-F.txt
        combined_txt = prompt_dir_path / f"{prompt_id}.txt"
        if combined_txt.exists():
            logger.info(f"Trovato file prompt {prompt_id}: {combined_txt}")
            return combined_txt
            
        # Cerca anche nel formato CM1.txt o CSF.txt (senza trattino)
        no_dash_txt = prompt_dir_path / f"{base_id}{sub_id}.txt"
        if no_dash_txt.exists():
            logger.info(f"Trovato file prompt {prompt_id}: {no_dash_txt}")
            return no_dash_txt
    
    # Fallback: cerca file che potrebbero corrispondere al prompt_id con ricerca più ampia
    for extension in ['.txt', '.docx']:
        # Cerca file che contengono l'ID del prompt
        for file_path in prompt_dir_path.glob(f"*{prompt_id}*{extension}"):
            logger.info(f"Trovato file prompt {prompt_id} con corrispondenza parziale: {file_path}")
            return file_path
        
        # Se c'è un trattino, prova anche senza
        if "-" in prompt_id:
            base_id, sub_id = prompt_id.split("-", 1)
            for file_path in prompt_dir_path.glob(f"*{base_id}*{sub_id}*{extension}"):
                logger.info(f"Trovato file prompt {prompt_id} con corrispondenza parziale: {file_path}")
                return file_path
    
    raise FileNotFoundError(f"Nessun file trovato per prompt ID {prompt_id}")

def parse_prompt_data(file_content):
    """
    Analizza il contenuto del file di prompt e ne estrae i componenti.
    Versione semplificata e robusta.
    
    Args:
        file_content: Contenuto testuale del prompt
        
    Returns:
        dict: Dati del prompt (metadata, variables, content)
    """
    print(f"DEBUG - Inizio parsing del prompt: {len(file_content)} caratteri")
    
    metadata_text = extract_section(file_content, "METADATA")
    variables_text = extract_section(file_content, "VARIABLES")
    prompt_text = extract_section(file_content, "PROMPT")
    
    # Estrai i valori dal metadata
    metadata = {}
    for line in metadata_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    
    # Estrai le variabili
    variables = [v.strip() for v in variables_text.split("\n") if v.strip()]
    
    # Se non è stato possibile estrarre le variabili, usa default
    if not variables:
        variables = ["KEYWORD", "MERCATO", "LINGUA"]
        print("DEBUG - Nessuna variabile trovata, usando default")
    
    # Se non è stato possibile estrarre il prompt, usa un fallback
    if not prompt_text:
        print("DEBUG - ERRORE: Impossibile estrarre il prompt - usando fallback")
        prompt_text = (
            "Fornisci una definizione chiara e completa di cosa rappresenta \"{KEYWORD}\" "
            "nel contesto del mercato {MERCATO}..."
        )
    else:
        print(f"DEBUG - Prompt estratto con successo: {len(prompt_text)} caratteri")
        print(f"DEBUG - Primi 50 caratteri: {prompt_text[:50]}...")
    
    return {
        "metadata": metadata,
        "variables": variables,
        "content": prompt_text
    }
