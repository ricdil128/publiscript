"""
Utilità per gestione file e testo.
"""

import re
import os
import json

# ============================================================
# FUNZIONI DI UTILITÀ FILE E TESTO
# ============================================================
def sanitize_filename(name):
    """Rimuove caratteri non validi dai nomi file."""
    return re.sub(r'[<>:"/\\|?*]', '', name)

def clean_text(text):
    """Pulisce il testo rimuovendo caratteri non ASCII e non stampabili."""
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = ''.join(char for char in text if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) < 127))
    return text

def split_text(text, chunk_size=1000):
    """Divide il testo in blocchi di dimensione adeguata senza spezzare le parole."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def load_config():
    """Carica la configurazione dal file JSON."""
    with open("config.json", "r", encoding="utf-8") as file:
        return json.load(file)

def check_unresolved_placeholders(text):
    """
    Verifica placeholders non risolti nel testo
    
    Args:
        text: Testo da controllare
        
    Returns:
        list: Lista di placeholders non risolti o None se non ce ne sono
    """
    import re
    placeholders = re.findall(r'\{([A-Za-z_]+)\}', text)
    return placeholders if placeholders else None