"""
Analisi buyer persona per CRISP.
"""

import re

def extract_buyer_persona(text):
    """
    Estrae la buyer persona (CS-2).
    
    Args:
        text: Risposta da Genspark per prompt CS-2
        
    Returns:
        dict: Dati strutturati sulla buyer persona
    """
    data = {}
    
    # Estrai BUYER_PERSONA_SUMMARY
    persona_section = re.search(r'BUYER_PERSONA_SUMMARY[^:]*:(.*?)(?=ONLINE_BEHAVIOR_INSIGHTS|$)', 
                               text, re.DOTALL | re.IGNORECASE)
    if persona_section:
        data["BUYER_PERSONA_SUMMARY"] = persona_section.group(1).strip()
    
    # Estrai ONLINE_BEHAVIOR_INSIGHTS
    behavior_section = re.search(r'ONLINE_BEHAVIOR_INSIGHTS[^:]*:(.*?)(?=END|$)', 
                                text, re.DOTALL | re.IGNORECASE)
    if behavior_section:
        data["ONLINE_BEHAVIOR_INSIGHTS"] = behavior_section.group(1).strip()
    
    return data

def extract_angle_of_attack(text):
    """
    Estrae l'angolo di attacco (CS-3).
    
    Args:
        text: Risposta da Genspark per prompt CS-3
        
    Returns:
        dict: Dati strutturati sull'angolo di attacco
    """
    data = {}
    
    # Estrai ANGOLO_ATTACCO
    angle_section = re.search(r'ANGOLO_ATTACCO[^:]*:(.*?)(?=PROMESSA_PRINCIPALE|$)', 
                             text, re.DOTALL | re.IGNORECASE)
    if angle_section:
        data["ANGOLO_ATTACCO"] = angle_section.group(1).strip()
    
    # Estrai PROMESSA_PRINCIPALE
    promise_section = re.search(r'PROMESSA_PRINCIPALE[^:]*:(.*?)(?=USP_ELEMENTS|$)', 
                               text, re.DOTALL | re.IGNORECASE)
    if promise_section:
        data["PROMESSA_PRINCIPALE"] = promise_section.group(1).strip()
    
    # Estrai USP_ELEMENTS
    usp_section = re.search(r'USP_ELEMENTS[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if usp_section:
        data["USP_ELEMENTS"] = usp_section.group(1).strip()
    
    return data

def extract_title_and_style(text):
    """
    Estrae titolo e stile narrativo (CP-2).
    
    Args:
        text: Risposta da Genspark per prompt CP-2
        
    Returns:
        dict: Dati strutturati su titolo e stile
    """
    data = {}
    
    # Estrai TITOLO_LIBRO
    title_section = re.search(r'TITOLO_LIBRO[^:]*:(.*?)(?=SOTTOTITOLO_LIBRO|$)', text, re.DOTALL | re.IGNORECASE)
    if title_section:
        data["TITOLO_LIBRO"] = title_section.group(1).strip()
    
    # Estrai SOTTOTITOLO_LIBRO
    subtitle_section = re.search(r'SOTTOTITOLO_LIBRO[^:]*:(.*?)(?=VOICE_STYLE|$)', text, re.DOTALL | re.IGNORECASE)
    if subtitle_section:
        data["SOTTOTITOLO_LIBRO"] = subtitle_section.group(1).strip()
    
    # Estrai VOICE_STYLE
    voice_section = re.search(r'VOICE_STYLE[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if voice_section:
        data["VOICE_STYLE"] = voice_section.group(1).strip()
    
    return data
