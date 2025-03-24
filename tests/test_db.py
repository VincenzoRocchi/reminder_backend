# test_db.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ["ENV"] = "testing"

from app.database import Base, engine, get_db
from app.models import user, business, reminder, notification

# Crea le tabelle
Base.metadata.create_all(bind=engine)

# Verifica che le tabelle esistano
from sqlalchemy import inspect
inspector = inspect(engine)
print("Tabelle create:")
for table in inspector.get_table_names():
    print(f"- {table}")

# Apre una sessione e prova ad accedere alla tabella users
db = next(get_db())
try:
    users = db.query(user.User).all()
    print(f"Numero di utenti: {len(users)}")
except Exception as e:
    print(f"Errore nell'accesso alla tabella users: {e}")
finally:
    db.close()