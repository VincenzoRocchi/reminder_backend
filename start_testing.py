"""
Script per avviare l'applicazione in modalità testing.
Questo script imposta automaticamente ENV=testing e avvia l'applicazione.
"""
import os
import uvicorn

if __name__ == "__main__":
    # Imposta l'ambiente su testing
    os.environ["ENV"] = "testing"
    print("Ambiente impostato su: testing")
    print("Database: SQLite (test.db)")
    
    # Avvia l'applicazione
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)