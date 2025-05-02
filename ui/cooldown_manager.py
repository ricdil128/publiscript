"""
Gestione cooldown per limitare richieste.
"""

import time
from datetime import datetime

class CooldownManager:
    """
    Gestisce le pause e i cooldown tra le richieste per evitare 
    sovraccarichi e richieste abortite.
    """
    def __init__(self):
        self.request_count = 0
        self.total_requests = 0
        self.last_request_time = datetime.now()
        self.session_start_time = datetime.now()
        
        # Configurazione dei limiti
        self.short_cooldown_threshold = 3      # Ogni 3 richieste
        self.medium_cooldown_threshold = 10    # Ogni 10 richieste
        self.long_cooldown_threshold = 25      # Ogni 25 richieste
        
        self.short_cooldown_time = 30          # 30 secondi
        self.medium_cooldown_time = 120        # 2 minuti
        self.long_cooldown_time = 300          # 5 minuti
        
        # Tempi minimi tra richieste
        self.min_request_interval = 10         # 10 secondi tra richieste normali
        self.min_section_interval = 30         # 30 secondi tra sezioni

    def track_request(self):
        """
        Registra una richiesta e applica il cooldown necessario.
        
        Returns:
            int: Tempo di attesa in secondi applicato
        """
        self.request_count += 1
        self.total_requests += 1
        
        # Calcola il tempo passato dall'ultima richiesta
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        
        # Applica sempre il tempo minimo tra richieste se necessario
        wait_time = max(0, self.min_request_interval - time_since_last)
        
        # Controlla se è necessario un cooldown
        if self.request_count % self.long_cooldown_threshold == 0:
            print(f"⏲️ Raggiunta soglia di cooldown LUNGO dopo {self.long_cooldown_threshold} richieste")
            print(f"⏲️ Pausa di {self.long_cooldown_time} secondi per evitare sovraccarichi...")
            wait_time = self.long_cooldown_time
            # Reset del contatore per ricominciare
            self.request_count = 0
        elif self.request_count % self.medium_cooldown_threshold == 0:
            print(f"⏲️ Raggiunta soglia di cooldown MEDIO dopo {self.medium_cooldown_threshold} richieste")
            print(f"⏲️ Pausa di {self.medium_cooldown_time} secondi per evitare sovraccarichi...")
            wait_time = self.medium_cooldown_time
        elif self.request_count % self.short_cooldown_threshold == 0:
            print(f"⏲️ Raggiunta soglia di cooldown BREVE dopo {self.short_cooldown_threshold} richieste")
            print(f"⏲️ Pausa di {self.short_cooldown_time} secondi per evitare sovraccarichi...")
            wait_time = self.short_cooldown_time
        
        # Pausa per il tempo calcolato
        if wait_time > 0:
            time.sleep(wait_time)
        
        # Aggiorna il timestamp dell'ultima richiesta
        self.last_request_time = datetime.now()
        
        return wait_time
    
    def track_section(self):
        """
        Registra il completamento di una sezione e applica la pausa necessaria.
        
        Returns:
            int: Tempo di attesa in secondi applicato
        """
        # Calcola il tempo passato dall'ultima richiesta
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        
        # Applica sempre il tempo minimo tra sezioni se necessario
        wait_time = max(0, self.min_section_interval - time_since_last)
        
        if wait_time > 0:
            print(f"⏲️ Pausa di {wait_time} secondi tra sezioni...")
            time.sleep(wait_time)
        
        # Aggiorna il timestamp dell'ultima richiesta
        self.last_request_time = datetime.now()
        
        return wait_time
    
    def get_session_stats(self):
        """
        Restituisce statistiche sulla sessione corrente.
        
        Returns:
            dict: Statistiche della sessione
        """
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        return {
            "total_requests": self.total_requests,
            "session_duration_minutes": round(session_duration, 2),
            "requests_per_minute": round(self.total_requests / max(1, session_duration), 2)
        }
