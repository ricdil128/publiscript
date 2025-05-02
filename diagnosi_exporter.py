# diagnosi_exporter.py - Script di test autonomo che non modifica il codice esistente
import os
import sys
import traceback

def diagnostica_esportazione():
    """Esegue una serie di test diagnostici per verificare i problemi di esportazione"""
    risultati = []
    
    print("🔍 Avvio diagnosi sistema di esportazione PubliScript...")
    
    # Test 1: Verifica esistenza file context.txt
    try:
        context_file = "context.txt"
        context_esiste = os.path.exists(context_file)
        risultati.append({
            "test": "Esistenza file context.txt",
            "risultato": "✅ Trovato" if context_esiste else "❌ Non trovato",
            "dettagli": f"Percorso cercato: {os.path.abspath(context_file)}"
        })
        
        if context_esiste:
            # Leggi dimensione e prime righe per verificare contenuto
            size = os.path.getsize(context_file)
            with open(context_file, "r", encoding="utf-8") as f:
                prime_righe = [next(f, None) for _ in range(5)]
                prime_righe = [r.strip() if r else "[EOF]" for r in prime_righe]
            
            risultati.append({
                "test": "Analisi file context.txt",
                "risultato": "✅ File leggibile" if size > 0 else "⚠️ File vuoto",
                "dettagli": f"Dimensione: {size} bytes\nPrime righe:\n" + "\n".join(prime_righe)
            })
    except Exception as e:
        risultati.append({
            "test": "Accesso file context.txt",
            "risultato": "❌ Errore",
            "dettagli": f"Eccezione: {str(e)}\n{traceback.format_exc()}"
        })
    
    # Test 2: Verifica esistenza directory output
    try:
        output_dir = os.path.join(os.getcwd(), "output")
        output_esiste = os.path.exists(output_dir)
        risultati.append({
            "test": "Esistenza directory output",
            "risultato": "✅ Trovata" if output_esiste else "⚠️ Non trovata (verrà creata)",
            "dettagli": f"Percorso: {output_dir}"
        })
    except Exception as e:
        risultati.append({
            "test": "Verifica directory output",
            "risultato": "❌ Errore",
            "dettagli": f"Eccezione: {str(e)}"
        })
    
    # Test 3: Verifica dipendenze per esportazione
    try:
        dipendenze = {
            "docx": False,
            "docx2pdf": False
        }
        
        try:
            import docx
            dipendenze["docx"] = True
        except ImportError:
            pass
            
        try:
            import docx2pdf
            dipendenze["docx2pdf"] = True
        except ImportError:
            pass
        
        risultati.append({
            "test": "Dipendenze per esportazione",
            "risultato": "✅ Tutte disponibili" if all(dipendenze.values()) else "⚠️ Alcune mancanti",
            "dettagli": "\n".join([f"{k}: {'✅ Installato' if v else '❌ Mancante'}" for k, v in dipendenze.items()])
        })
    except Exception as e:
        risultati.append({
            "test": "Verifica dipendenze",
            "risultato": "❌ Errore",
            "dettagli": f"Eccezione: {str(e)}"
        })
    
    # Stampa risultati
    print("\n=== RISULTATI DIAGNOSI ===\n")
    for r in risultati:
        print(f"TEST: {r['test']}")
        print(f"RISULTATO: {r['risultato']}")
        print(f"DETTAGLI: {r['dettagli']}")
        print("-" * 50)
    
    return risultati

if __name__ == "__main__":
    diagnostica_esportazione()