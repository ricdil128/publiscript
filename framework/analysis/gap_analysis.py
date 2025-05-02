"""
Analisi gap e review per CRISP.
"""

import re

def extract_review_analysis(text):
    """Estrae dati dalle recensioni."""
    data = {}
    negative_points = re.findall(r'[•\-*]\s*([^•\-*\n]+)', text)
    if negative_points:
        data["PUNTI_NEGATIVI"] = [p.strip() for p in negative_points if p.strip()]
    return data

def extract_strategic_insights(text):
    """
    Estrae insight strategici (CS-1).
    
    Args:
        text: Risposta da Genspark per prompt CS-1
        
    Returns:
        dict: Dati strutturati sugli insight strategici
    """
    data = {}
    
    # Estrai STRATEGIC_INSIGHTS
    strategic_section = re.search(r'STRATEGIC_INSIGHTS[^:]*:(.*?)(?=END|$)', text, re.DOTALL | re.IGNORECASE)
    if strategic_section:
        data["STRATEGIC_INSIGHTS"] = strategic_section.group(1).strip()
    
    return data
