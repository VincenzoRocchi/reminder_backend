import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.business import Business
from app.core.security import get_password_hash
from app.core.encryption import encryption_service
from app.core.exceptions import InvalidConfigurationError, SensitiveDataStorageError

# Database SQLite in memoria
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestBusiness(unittest.TestCase):
    """Test suite per il modello Business e le sue API"""
    
    def setUp(self):
        """Preparazione per ogni test"""
        # Crea le tabelle del database
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        
        # Crea un utente di test nel database
        self.test_user = User(
            email="test@example.com",
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)
        
        # Configura il client di test con una sovrascrittura della dipendenza get_db
        def override_get_db():
            try:
                yield self.db
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        
        # Configura il mock per get_current_user
        self.get_current_user_patcher = patch("app.api.dependencies.get_current_user")
        self.mock_get_current_user = self.get_current_user_patcher.start()
        self.mock_get_current_user.return_value = self.test_user
        
        # Crea un'istanza Business per test senza database
        self.business_model = Business(
            name="Test Business",
            description="Un business di test per unit testing",
            email="test@example.com",
            owner_id=self.test_user.id,
            is_active=True
        )
    
    def tearDown(self):
        """Pulizia dopo ogni test"""
        # Rimuove le sovrascritture di dipendenza
        app.dependency_overrides.clear()
        
        # Ferma i patcher
        self.get_current_user_patcher.stop()
        
        # Pulisce il database
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    # SEZIONE 1: TEST SUL SERVIZIO DI CRITTOGRAFIA
    
    def test_encryption_service(self):
        """Verifica il funzionamento del servizio di crittografia"""
        test_value = "test_password"
        encrypted = encryption_service.encrypt_string(test_value)
        self.assertNotEqual(encrypted, test_value)
        decrypted = encryption_service.decrypt_string(encrypted)
        self.assertEqual(decrypted, test_value)
    
    # SEZIONE 2: TEST SULLE OPERAZIONI API DI BUSINESS
    
    def test_create_business(self):
        """Verifica la creazione di un'azienda tramite API"""
        business_data = {
            "name": "Azienda Test",
            "email": "test@azienda.it",
            "description": "Test descrizione"
        }
        response = self.client.post(
            "/api/v1/businesses/",
            json=business_data,
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], business_data["name"])
        self.assertIn("id", data)
    
    def test_get_business(self):
        """Verifica il recupero di un'azienda tramite API"""
        business = Business(
            name="Azienda Test",
            email="test@test.it",
            owner_id=self.test_user.id
        )
        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)
        
        response = self.client.get(
            f"/api/v1/businesses/{business.id}",
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], business.name)
    
    def test_update_business(self):
        """Verifica l'aggiornamento di un'azienda tramite API"""
        business = Business(
            name="Azienda Test",
            email="test@test.it",
            owner_id=self.test_user.id
        )
        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)
        
        update_data = {
            "name": "Nome Aggiornato"
        }
        response = self.client.put(
            f"/api/v1/businesses/{business.id}",
            json=update_data,
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], update_data["name"])
    
    def test_delete_business(self):
        """Verifica l'eliminazione di un'azienda tramite API"""
        business = Business(
            name="Azienda Test",
            email="test@test.it",
            owner_id=self.test_user.id
        )
        self.db.add(business)
        self.db.commit()
        self.db.refresh(business)
        
        response = self.client.delete(
            f"/api/v1/businesses/{business.id}",
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 204)
        
        response = self.client.get(
            f"/api/v1/businesses/{business.id}",
            headers={"Authorization": "Bearer test_token"}
        )
        self.assertEqual(response.status_code, 404)
    
    # SEZIONE 3: TEST SULLA CRITTOGRAFIA DEL MODELLO BUSINESS
    
    def test_phone_number_encryption(self):
        """Verifica che il numero di telefono sia criptato e decriptato correttamente"""
        # Imposta un numero di telefono
        test_phone = "+1234567890"
        self.business_model.phone_number = test_phone
        
        # Verifica che il valore criptato sia diverso dall'originale
        self.assertNotEqual(self.business_model._phone_number, test_phone)
        
        # Verifica che la decriptazione funzioni correttamente
        self.assertEqual(self.business_model.phone_number, test_phone)
    
    def test_smtp_password_encryption(self):
        """Verifica la cifratura e decifratura della password SMTP"""
        # Imposta credenziali SMTP
        self.business_model.smtp_host = "smtp.example.com"
        self.business_model.smtp_port = 587
        self.business_model.smtp_user = "user@example.com"
        
        # Imposta e testa la password
        test_password = "PasswordSicura123!"
        self.business_model.smtp_password = test_password
        
        # Verifica che il valore criptato sia diverso dall'originale
        self.assertNotEqual(self.business_model._smtp_password, test_password)
        
        # Verifica che la decriptazione funzioni correttamente
        self.assertEqual(self.business_model.smtp_password, test_password)
    
    def test_twilio_token_encryption(self):
        """Verifica la cifratura del token Twilio e la sua validazione"""
        # Imposta credenziali Twilio valide (token iniziano con SK e sono 32 caratteri)
        self.business_model.twilio_account_sid = "AC0123456789abcdef0123456789abcdef"
        valid_token = "SK0123456789abcdef0123456789abcdef"
        
        # Test con un token formattato correttamente
        self.business_model.twilio_auth_token = valid_token
        self.assertEqual(self.business_model.twilio_auth_token, valid_token)
    
    def test_twilio_validation_non_strict(self):
        """Verifica che la validazione sia bypassata quando non in modalità stretta"""
        with patch('app.core.settings.Settings.should_validate', return_value=False):
            business = Business(
                name="Test Business",
                owner_id=1
            )
            # Imposta un token non valido (troppo corto e prefisso sbagliato)
            invalid_token = "INVALID123"
            business.twilio_account_sid = "ACsomeaccountid"
            
            # Questo dovrebbe funzionare quando la validazione stretta è disattivata
            business.twilio_auth_token = invalid_token
            self.assertEqual(business.twilio_auth_token, invalid_token)
    
    def test_twilio_validation_strict(self):
        """Verifica che la validazione sollevi un'eccezione in modalità stretta"""
        with patch('app.core.settings.settings.should_validate', return_value=True):
            with patch('app.core.settings.settings.STRICT_VALIDATION', True):
                business = Business(
                    name="Test Business",
                    owner_id=1
                )
                # Imposta un token non valido (troppo corto e prefisso sbagliato)
                invalid_token = "INVALID123"
                business.twilio_account_sid = "ACsomeaccountid"
                
                # Questo dovrebbe generare un errore di validazione
                with self.assertRaises(InvalidConfigurationError):
                    business.twilio_auth_token = invalid_token
    
    def test_encryption_failure_handling(self):
        """Verifica la gestione dei fallimenti di cifratura"""
        # Simula un fallimento del servizio di cifratura
        with patch.object(encryption_service, 'encrypt_string', side_effect=Exception("Encryption failed")):
            with self.assertRaises(SensitiveDataStorageError):
                self.business_model.phone_number = "+1234567890"

if __name__ == '__main__':
    unittest.main()