from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Crea il motore del database
engine = create_engine(settings.database_url)
# Crea una sessione per le operazioni con il DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base per i modelli SQLAlchemy
Base = declarative_base()

# Funzione per ottenere la sessione del database
def get_db():
    db = SessionLocal()
    try:
        yield db  # Restituisce la sessione
    finally:
        db.close()  # Chiude la sessione dopo l'uso
