"""
Utilità per gestione log.
"""

import logging
from datetime import datetime

def setup_logger(name, log_file="genschat.log", level=logging.INFO):
    """Configura e restituisce un logger"""
    # Configurazione del logger
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger