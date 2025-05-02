"""
Estrattori per il framework CRISP.
"""

import re
import json
import logging

# Import dalle sottodirectory
from .analysis.market_analysis import extract_market_analysis
from .analysis.buyer_persona import extract_buyer_persona
from .analysis.gap_analysis import extract_review_analysis

# Configurazione logging
logger = logging.getLogger("crisp_extractors")

#crisp_extractors.py

"""
Estrattori specializzati per il framework CRISP.
Contiene funzioni per estrarre dati strutturati dalle risposte di Genspark.
"""

def extract_data_from_response(response_text, prompt_id):
    """
    Estrattore principale che smista a funzioni specializzate in base al prompt_id.
    
    Args:
        response_text: Risposta da Genspark
        prompt_id: ID del prompt (es. "CM-1", "CS-2")
        
    Returns:
        dict: Dati estratti in formato strutturato
    """
    # Prima verifica se la risposta è vuota
    if not response_text:
        logger.warning(f"Risposta vuota per {prompt_id}")
        return {}
    
    # Aggiungi questi log di debug
    print(f"DEBUG FINE CHECK: Prompt ID: {prompt_id}")
    print(f"DEBUG FINE CHECK: Lunghezza response_text: {len(response_text)}")
    print(f"DEBUG FINE CHECK: response_text contiene 'FINE_RISPOSTA': {'FINE_RISPOSTA' in response_text}")
    print(f"DEBUG FINE CHECK: response_text contiene 'FINE': {'FINE' in response_text}")
    print(f"DEBUG FINE CHECK: Ultimi 50 caratteri di response_text: {response_text[-50:] if len(response_text) > 50 else response_text}")
    
    # Verifica se la risposta contiene FINE o FINE_RISPOSTA
    has_end = "FINE_RISPOSTA" in response_text or "FINE" in response_text
    if not has_end:
        logger.warning(f"Risposta incompleta per {prompt_id} - manca FINE o FINE_RISPOSTA")
    
        # Per CM-1, forniamo comunque i valori di fallback
        if prompt_id == "CM-1":
            logger.info(f"Fornendo valori di fallback per {prompt_id} nonostante manchi FINE_RISPOSTA")
            return {
                "MARKET_INSIGHTS": "Analisi di mercato completata",
                "BESTSELLER_OVERVIEW": "Panoramica bestseller completata", 
                "KEYWORD_DATA": "Dati keyword analizzati"
            }
        return {}
    
    # Estrai solo il contenuto fino a FINE
    if "FINE_RISPOSTA" in response_text:
        response_text = response_text.split("FINE_RISPOSTA")[0].strip()
    elif "FINE" in response_text:
        response_text = response_text.split("FINE")[0].strip()

    logger.info(f"Processando risposta completa per {prompt_id} ({len(response_text)} chars)")

    # Mappa degli estrattori specializzati per i prompt CRISP 5.0
    extractors = {
        # Analisi Fondazionale
        "CM-1": extract_market_analysis,
        "CM-2": extract_bestseller_analysis,
        
        # Strategia di Posizionamento
        "CS-1": extract_strategic_insights,
        "CS-2": extract_buyer_persona,
        "CS-3": extract_angle_of_attack,
        
        # Sviluppo del Prodotto
        "CP-1": extract_product_structure,
        "CP-2": extract_title_and_style,
        
        # Marketing e Promozione
        "CPM-1": extract_marketing_strategy,
        "CPM-2": extract_cover_brief,
        "CPM-3": extract_post_purchase_support,
        
        # Sintesi Finale
        "CS-F": extract_final_synthesis
    }
    
    # Mappa delle variabili critiche per ogni fase
    critical_vars = {
        "CM-1": ["MARKET_INSIGHTS", "BESTSELLER_OVERVIEW", "KEYWORD_DATA"],
        "CS-1": ["STRATEGIC_INSIGHTS"],
        "CS-2": ["BUYER_PERSONA_SUMMARY", "ONLINE_BEHAVIOR_INSIGHTS"],
        "CS-3": ["ANGOLO_ATTACCO", "PROMESSA_PRINCIPALE"],
        "CP-1": ["BOOK_JOURNEY", "BIG_IDEA", "CONTENT_PILLARS", "PROPRIETARY_METHOD"],
        "CP-2": ["TITOLO_LIBRO", "SOTTOTITOLO_LIBRO", "VOICE_STYLE"],
        "CPM-1": ["MARKETING_CLAIMS", "HEADLINE_OPTIONS", "AMAZON_DESCRIPTION"],
        "CPM-2": ["COVER_BRIEF", "VISUAL_ELEMENTS"],
        "CPM-3": ["BONUS_SYSTEM", "EMAIL_STRATEGY"],
        "CS-F": ["FINAL_SYNTHESIS"]
    }
    
    # Seleziona l'estrattore appropriato o usa un estrattore generico
    extractor = extractors.get(prompt_id, extract_generic)
    
    try:
        extracted_data = extractor(response_text)
        
        # Verifica e fornisci valori di fallback per le variabili critiche
        if prompt_id in critical_vars:
            # Per ogni variabile critica, verifica che sia presente e non vuota
            for var in critical_vars[prompt_id]:
                if var not in extracted_data or not extracted_data[var]:
                    # Log del fallback
                    logger.warning(f"Variabile critica {var} mancante in {prompt_id}, utilizzo valore di fallback")
                    # Assegna un valore di fallback
                    extracted_data[var] = f"Valore di fallback per {var} da {prompt_id}"
        
        logger.info(f"Estrazione dati completata per {prompt_id}: {len(extracted_data)} elementi")
        return extracted_data
    except Exception as e:
        logger.error(f"Errore durante l'estrazione dati per {prompt_id}: {str(e)}")
        
        # Fornisci valori di fallback per variabili critiche in caso di errore
        fallback_data = {"error": str(e), "raw_text": response_text}
        
        # Se questo prompt_id ha variabili critiche definite
        if prompt_id in critical_vars:
            for var in critical_vars[prompt_id]:
                fallback_data[var] = f"Valore di fallback per {var} da {prompt_id} dopo errore"
        else:
            # Fallback specifico per CM-1 (per compatibilità con codice esistente)
            if prompt_id == "CM-1":
                fallback_data["MARKET_INSIGHTS"] = "Analisi di mercato completata"
                fallback_data["BESTSELLER_OVERVIEW"] = "Panoramica bestseller completata"
                fallback_data["KEYWORD_DATA"] = "Dati keyword analizzati"
        
        return fallback_data

def extract_generic(text):
    """
    Estrattore generico per prompt senza estrattore specializzato.
    
    Args:
        text: Risposta da Genspark
        
    Returns:
        dict: Dati estratti in forma base
    """
    # Rimuovi markdown e formattazione in eccesso
    cleaned_text = re.sub(r'#+\s+', '', text)  # Rimuove header markdown
    
    # Cerca di estrarre sezioni
    sections = {}
    current_section = "general"
    sections[current_section] = []
    
    for line in cleaned_text.split('\n'):
        # Cerca intestazioni di sezione
        section_match = re.match(r'^([A-Z][A-Za-z\s]+):$', line)
        if section_match:
            current_section = section_match.group(1).strip().lower().replace(' ', '_')
            sections[current_section] = []
            continue
        
        # Aggiungi la linea alla sezione corrente
        if line.strip():
            sections[current_section].append(line.strip())
    
    # Converti le liste in stringhe per sezioni con una sola linea
    for section, lines in sections.items():
        if len(lines) == 1:
            sections[section] = lines[0]
        elif len(lines) > 1:
            sections[section] = '\n'.join(lines)
        else:
            sections[section] = ""
    
    # Aggiungi il testo originale
    sections["raw_text"] = text
    
    return sections

def extract_keyword_analysis(text):
    """
    Estrae dati dalla risposta di analisi keyword (C1).
    
    Args:
        text: Risposta da Genspark per prompt C1
        
    Returns:
        dict: Dati strutturati sull'analisi delle keyword
    """
    data = {}
    
    # Estrai la keyword principale
    keyword_match = re.search(r'keyword "([^"]+)"', text, re.IGNORECASE)
    if keyword_match:
        data["KEYWORD_PRINCIPALE"] = keyword_match.group(1)
    
    # Estrai la valutazione di profittabilità
    profitability_match = re.search(r'profittabilit[àa].*?(\d+)[/\\]10', text, re.IGNORECASE)
    if profitability_match:
        data["PROFITTABILITA"] = int(profitability_match.group(1))
    
    # Estrai cluster di keyword
    clusters = []
    cluster_sections = re.findall(r'Cluster \d+[^:]*:(.*?)(?=Cluster \d+|$)', text, re.DOTALL)
    for i, section in enumerate(cluster_sections, 1):
        keywords = re.findall(r'[•\-*]\s*([^•\-*\n]+)', section)
        if keywords:
            clusters.append({
                "nome": f"Cluster {i}",
                "keywords": [k.strip() for k in keywords if k.strip()]
            })
    
    if clusters:
        data["CLUSTERS"] = clusters
        # Estrai anche le keyword correlate come lista piatta
        all_related = []
        for cluster in clusters:
            all_related.extend(cluster["keywords"])
        data["KEYWORDS_CORRELATE"] = all_related
    
    # Estrai informazioni sul mercato
    market_size_match = re.search(r'mercato.*?(\$[\d.,]+ [mb]i?llion)', text, re.IGNORECASE)
    if market_size_match:
        data["DIMENSIONE_MERCATO"] = market_size_match.group(1)
    
    # Estrai il volume di ricerca
    volume_match = re.search(r'volume di ricerca.*?(basso|medio|alto)', text, re.IGNORECASE)
    if volume_match:
        data["VOLUME_RICERCA"] = volume_match.group(1).lower()
    
    # Estrai gap di mercato
    gaps = re.findall(r'[•\-*]\s*(gap[^•\-*\n]+)', text, re.IGNORECASE)
    if gaps:
        data["GAP_MERCATO"] = [g.strip() for g in gaps if g.strip()]
    
    return data

def extract_buyer_persona(text):
    """
    Estrae dati della buyer persona (C2).
    
    Args:
        text: Risposta da Genspark per prompt C2
        
    Returns:
        dict: Dati strutturati sulla buyer persona
    """
    data = {}
    
    # Estrai dati demografici
    age_match = re.search(r'et[àa][:\s]+(\d+)[^\d]*(\d+)', text, re.IGNORECASE)
    if age_match:
        data["ETA_MIN"] = int(age_match.group(1))
        data["ETA_MAX"] = int(age_match.group(2))
    
    gender_match = re.search(r'gener[eo][:\s]+([\w\s]+?)(?:\(|,|\.|$)', text, re.IGNORECASE)
    if gender_match:
        data["GENERE"] = gender_match.group(1).strip()
    
    # Estrai motivazioni principali
    motivations = []
    motivation_section = re.search(r'motivazion[ie][:\s]+(.*?)(?=\n\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
    if motivation_section:
        motivation_points = re.findall(r'[•\-*]\s*([^•\-*\n]+)', motivation_section.group(1))
        motivations = [m.strip() for m in motivation_points if m.strip()]
    
    if motivations:
        data["MOTIVAZIONI"] = motivations
    
    # Estrai problemi e dolori
    pains = []
    pain_section = re.search(r'(problemi|dolori|sfide)[:\s]+(.*?)(?=\n\s*\n|$)', text, re.IGNORECASE | re.DOTALL)
    if pain_section:
        pain_points = re.findall(r'[•\-*]\s*([^•\-*\n]+)', pain_section.group(2))
        pains = [p.strip() for p in pain_points if p.strip()]
    
    if pains:
        data["PROBLEMI"] = pains
    
    # Crea una sintesi della buyer persona
    summary_parts = []
    if "ETA_MIN" in data and "ETA_MAX" in data:
        summary_parts.append(f"{data['ETA_MIN']}-{data['ETA_MAX']} anni")
    if "GENERE" in data:
        summary_parts.append(data["GENERE"])
    if "MOTIVAZIONI" in data and len(data["MOTIVAZIONI"]) > 0:
        summary_parts.append(f"cerca {data['MOTIVAZIONI'][0].lower()}")
    if "PROBLEMI" in data and len(data["PROBLEMI"]) > 0:
        summary_parts.append(f"affronta {data['PROBLEMI'][0].lower()}")
    
    if summary_parts:
        data["BUYER_PERSONA_SUMMARY"] = ", ".join(summary_parts)
    
    return data

def extract_tone_style(text):
    """
    Estrae informazioni sullo stile e tono narrativo (S1).
    
    Args:
        text: Risposta da Genspark per prompt S1
        
    Returns:
        dict: Dati strutturati su stile e tono
    """
    data = {}
    
    # Estrai la personalità narrativa
    personality_section = re.search(r'Personalit[àa] Narrativa[:\s]+(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if personality_section:
        identity_match = re.search(r'Identit[àa][^:]*:[^\n]*\n*\s*([^\n]+)', personality_section.group(1), re.IGNORECASE)
        if identity_match:
            data["IDENTITA_NARRATIVA"] = identity_match.group(1).strip()
    
    # Estrai livello di formalità
    formality_match = re.search(r'formalit[àa][^:]*:[^\n]*\n*\s*(\d+)[/\\]10', text, re.IGNORECASE)
    if formality_match:
        data["LIVELLO_FORMALITA"] = int(formality_match.group(1))
    
    # Estrai esempi di aperture capitoli
    openings = []
    openings_section = re.search(r'Aperture di Capitolo[:\s]+(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if openings_section:
        opening_examples = re.findall(r'\d+\.\s+"([^"]+)"', openings_section.group(1))
        if not opening_examples:
            opening_examples = re.findall(r'\d+\.\s*([^\d\n]+)', openings_section.group(1))
        openings = [o.strip() for o in opening_examples if o.strip()]
    
    if openings:
        data["ESEMPI_APERTURE"] = openings
    
    # Estrai vocabolario di trasformazione
    vocabulary = []
    vocab_section = re.search(r'Vocabolario di Trasformazione[:\s]+(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if vocab_section:
        terms = re.findall(r'[•\-*]\s*"([^"]+)"', vocab_section.group(1))
        if not terms:
            terms = re.findall(r'[•\-*]\s*([^•\-*\n]+)', vocab_section.group(1))
        vocabulary = [t.strip() for t in terms if t.strip()]
    
    if vocabulary:
        data["LEXICON_TRASFORMAZIONE"] = vocabulary
    
    # Estrai la curva emotiva
    emotion_match = re.search(r'curva emotiva[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if emotion_match:
        data["CURVA_EMOTIVA"] = emotion_match.group(1).strip()
    
    # Crea una sintesi dello stile
    style_parts = []
    if "IDENTITA_NARRATIVA" in data:
        style_parts.append(data["IDENTITA_NARRATIVA"])
    if "LIVELLO_FORMALITA" in data:
        if data["LIVELLO_FORMALITA"] <= 3:
            style_parts.append("stile informale")
        elif data["LIVELLO_FORMALITA"] <= 7:
            style_parts.append("stile bilanciato")
        else:
            style_parts.append("stile formale")
    if "CURVA_EMOTIVA" in data:
        style_parts.append(f"con arco emotivo: {data['CURVA_EMOTIVA']}")
    
    if style_parts:
        data["STILE_SUMMARY"] = ", ".join(style_parts)
    
    return data

# NUOVE FUNZIONI ESTRATTORE

def extract_competition_analysis(text):
    """
    Estrae l'analisi della competizione dalla risposta.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti, inclusa la variabile TOPN
    """
    data = {}
    
    # Estrai TOPN - cerca i top seller/competitor 
    topn_pattern = r"(?i)(?:top|migliori|principali)\s*(?:seller|competitor|concorrenti|libri)(?:[:\s]+)([^\.]+)"
    topn_match = re.search(topn_pattern, text)
    
    if topn_match:
        topn_text = topn_match.group(1).strip()
        # Pulisci e formatta i risultati
        data['TOPN'] = topn_text
    else:
        # Valore di fallback se non troviamo nulla
        data['TOPN'] = "Non trovato, assegnato valore predefinito"
    
    # Estrai singoli competitor
    competitor_pattern = r"(?i)(?:competitor|concorrente|libro concorrente|bestseller)[^\n]*?[:\s]+([^\n\.]+)"
    competitor_matches = re.finditer(competitor_pattern, text)
    
    competitors = []
    for i, match in enumerate(competitor_matches):
        if i < 3:  # Prendi solo i primi 3
            competitors.append(match.group(1).strip())
    
    # Assegna i competitor trovati
    for i, comp in enumerate(competitors):
        data[f'COMPETITOR{i+1}'] = comp
    
    # Assicurati che ci siano almeno 3 competitor
    for i in range(1, 4):
        if f'COMPETITOR{i}' not in data:
            data[f'COMPETITOR{i}'] = f"Competitor {i} non trovato"
    
    return data

def extract_angle_of_attack(text):
    """
    Estrae l'angolo di attacco per il libro.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi all'angolo di attacco
    """
    data = {}
    
    # Estrai l'angolo di attacco principale
    angle_match = re.search(r'(?:angolo|approccio)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if angle_match:
        data["ANGOLO_ATTACCO"] = angle_match.group(1).strip()
    else:
        data["ANGOLO_ATTACCO"] = "Angolo di attacco non identificato"
    
    # Estrai la promessa principale
    promise_match = re.search(r'(?:promessa|beneficio)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if promise_match:
        data["PROMESSA_PRINCIPALE"] = promise_match.group(1).strip()
    
    return data

def extract_title_subtitle(text):
    """
    Estrae titolo e sottotitolo per il libro.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi al titolo
    """
    data = {}
    
    # Estrai il titolo principale
    title_match = re.search(r'(?:Titolo|Titolo principale)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if title_match:
        data["TITOLO_LIBRO"] = title_match.group(1).strip().strip('"\'')
    
    # Estrai il sottotitolo
    subtitle_match = re.search(r'(?:Sottotitolo)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if subtitle_match:
        data["SOTTOTITOLO_LIBRO"] = subtitle_match.group(1).strip().strip('"\'')
    
    return data

def extract_marketing_claims(text):
    """
    Estrae claim di marketing.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi ai claim marketing
    """
    data = {}
    claims = re.findall(r'[•\-*]\s*([^•\-*\n]+)', text)
    if claims:
        data["MARKETING_CLAIMS"] = [c.strip() for c in claims if c.strip()]
        data["LISTA_BENEFICI"] = data["MARKETING_CLAIMS"][:3]  # Primi 3 come benefici principali
    return data

def extract_amazon_description(text):
    """
    Estrae la descrizione per Amazon.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi alla descrizione Amazon
    """
    data = {}
    description = re.search(r'(?:Descrizione|Testo descrizione)[^:]*:(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if description:
        data["DESCRIZIONE_AMAZON"] = description.group(1).strip()
    return data

def extract_cover_brief(text):
    """
    Estrae brief per la copertina.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi al brief copertina
    """
    data = {}
    elements = re.findall(r'(?:Elementi|Colori|Stile|Mood)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if elements:
        data["BRIEF_COPERTINA"] = "\n".join(elements)
    return data

def extract_bonus_pdf(text):
    """
    Estrae informazioni sul bonus PDF.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi al bonus PDF
    """
    data = {}
    title_match = re.search(r'(?:Titolo PDF|Nome bonus)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if title_match:
        data["TITOLO_BONUS"] = title_match.group(1).strip()
    
    content_match = re.search(r'(?:Contenuto|Elementi)[^:]*:(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if content_match:
        data["CONTENUTO_BONUS"] = content_match.group(1).strip()
    
    return data

def extract_email_followup(text):
    """
    Estrae email di follow-up.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi all'email follow-up
    """
    data = {}
    subject_match = re.search(r'(?:Oggetto|Subject)[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if subject_match:
        data["EMAIL_OGGETTO"] = subject_match.group(1).strip()
    
    body_match = re.search(r'(?:Corpo|Body|Testo)[^:]*:(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if body_match:
        data["EMAIL_CORPO"] = body_match.group(1).strip()
    
    return data

def extract_strategic_prompt(text):
    """
    Estrae prompt strategico.
    
    Args:
        text: Testo della risposta
        
    Returns:
        dict: Dati estratti relativi al prompt strategico
    """
    data = {}
    # Estrai la visione strategica
    vision_match = re.search(r'(?:Visione|Strategia)[^:]*:(.*?)(?=###|##|$)', text, re.DOTALL | re.IGNORECASE)
    if vision_match:
        data["PROMPT_STRATEGICO"] = vision_match.group(1).strip()
    return data

# Placeholder per funzioni mancanti indicate nel dizionario

def extract_recipe_blueprint(text):
    """Estrae blueprint/struttura."""
    data = {}
    sections = re.findall(r'(?:Sezione|Capitolo|Parte)\s+\d+[^:]*:[^\n]*\n*\s*([^\n]+)', text, re.IGNORECASE)
    if sections:
        data["SEZIONI"] = sections
    return data

def extract_title_bestseller_analysis(text):
    """Estrae analisi dei titoli bestseller."""
    data = {}
    titles = re.findall(r'\d+\.\s+"([^"]+)"', text)
    if titles:
        data["TITOLI_BESTSELLER"] = titles
    return data


def extract_product_structure(text):
    """
    Estrae la struttura del prodotto (CP-1).
    
    Args:
        text: Risposta da Genspark per prompt CP-1
        
    Returns:
        dict: Dati strutturati sulla struttura del prodotto
    """
    data = {}
    
    # Estrai BOOK_JOURNEY
    journey_section = re.search(r'BOOK_JOURNEY[^:]*:(.*?)(?=BIG_IDEA|$)', text, re.DOTALL | re.IGNORECASE)
    if journey_section:
        data["BOOK_JOURNEY"] = journey_section.group(1).strip()
    
    # Estrai BIG_IDEA
    idea_section = re.search(r'BIG_IDEA[^:]*:(.*?)(?=CONTENT_PILLARS|$)', text, re.DOTALL | re.IGNORECASE)
    if idea_section:
        data["BIG_IDEA"] = idea_section.group(1).strip()
    
    # Estrai CONTENT_PILLARS
    pillars_section = re.search(r'CONTENT_PILLARS[^:]*:(.*?)(?=PROPRIETARY_METHOD|$)', text, re.DOTALL | re.IGNORECASE)
    if pillars_section:
        data["CONTENT_PILLARS"] = pillars_section.group(1).strip()
    
    # Estrai PROPRIETARY_METHOD
    method_section = re.search(r'PROPRIETARY_METHOD[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if method_section:
        data["PROPRIETARY_METHOD"] = method_section.group(1).strip()
    
    return data


def extract_marketing_strategy(text):
    """
    Estrae la strategia di marketing (CPM-1).
    
    Args:
        text: Risposta da Genspark per prompt CPM-1
        
    Returns:
        dict: Dati strutturati sulla strategia di marketing
    """
    data = {}
    
    # Estrai MARKETING_CLAIMS
    claims_section = re.search(r'MARKETING_CLAIMS[^:]*:(.*?)(?=HEADLINE_OPTIONS|$)', text, re.DOTALL | re.IGNORECASE)
    if claims_section:
        data["MARKETING_CLAIMS"] = claims_section.group(1).strip()
    
    # Estrai HEADLINE_OPTIONS
    headline_section = re.search(r'HEADLINE_OPTIONS[^:]*:(.*?)(?=AMAZON_DESCRIPTION|$)', text, re.DOTALL | re.IGNORECASE)
    if headline_section:
        data["HEADLINE_OPTIONS"] = headline_section.group(1).strip()
    
    # Estrai AMAZON_DESCRIPTION
    amazon_section = re.search(r'AMAZON_DESCRIPTION[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if amazon_section:
        data["AMAZON_DESCRIPTION"] = amazon_section.group(1).strip()
    
    return data

def extract_cover_brief(text):
    """
    Estrae il brief per la copertina (CPM-2).
    
    Args:
        text: Risposta da Genspark per prompt CPM-2
        
    Returns:
        dict: Dati strutturati sul brief della copertina
    """
    data = {}
    
    # Estrai COVER_BRIEF
    cover_section = re.search(r'COVER_BRIEF[^:]*:(.*?)(?=VISUAL_ELEMENTS|$)', text, re.DOTALL | re.IGNORECASE)
    if cover_section:
        data["COVER_BRIEF"] = cover_section.group(1).strip()
    
    # Estrai VISUAL_ELEMENTS
    visual_section = re.search(r'VISUAL_ELEMENTS[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if visual_section:
        data["VISUAL_ELEMENTS"] = visual_section.group(1).strip()
    
    return data

def extract_post_purchase_support(text):
    """
    Estrae il sistema di supporto post-acquisto (CPM-3).
    
    Args:
        text: Risposta da Genspark per prompt CPM-3
        
    Returns:
        dict: Dati strutturati sul supporto post-acquisto
    """
    data = {}
    
    # Estrai BONUS_SYSTEM
    bonus_section = re.search(r'BONUS_SYSTEM[^:]*:(.*?)(?=EMAIL_STRATEGY|$)', text, re.DOTALL | re.IGNORECASE)
    if bonus_section:
        data["BONUS_SYSTEM"] = bonus_section.group(1).strip()
    
    # Estrai EMAIL_STRATEGY
    email_section = re.search(r'EMAIL_STRATEGY[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if email_section:
        data["EMAIL_STRATEGY"] = email_section.group(1).strip()
    
    return data

def extract_final_synthesis(text):
    """
    Estrae la sintesi finale (CS-F).
    
    Args:
        text: Risposta da Genspark per prompt CS-F
        
    Returns:
        dict: Dati strutturati sulla sintesi finale
    """
    data = {}
    
    # Estrai FINAL_SYNTHESIS
    final_section = re.search(r'FINAL_SYNTHESIS[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if final_section:
        data["FINAL_SYNTHESIS"] = final_section.group(1).strip()
    
    # Estrai anche eventuali altre sezioni di sintesi
    sections = [
        "MARKET_SUMMARY", "POSITIONING_SUMMARY", "PRODUCT_SUMMARY", "MARKETING_SUMMARY",
        "NEXT_STEPS", "RECOMMENDATIONS"
    ]
    
    for section in sections:
        section_match = re.search(f'{section}[^:]*:(.*?)(?=\n[A-Z_]+:|$)', text, re.DOTALL | re.IGNORECASE)
        if section_match:
            data[section] = section_match.group(1).strip()
    
    return data