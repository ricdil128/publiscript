"""
Configurazione per PubliScript.
"""

# Configurazioni del framework CRISP
CRISP_CONFIG = {
    "prompt_dir": "prompt_crisp",
    "database_path": "crisp_projects.db"
}

# Configurazioni dell'interfaccia
UI_CONFIG = {
    "theme": "soft",
    "port": 7860
}

# Configurazioni del browser
BROWSER_CONFIG = {
    "headless": False,
    "disable_images": False
}