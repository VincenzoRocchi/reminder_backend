from pydantic import BaseModel, EmailStr
from datetime import date

class CustomerBase(BaseModel):
    name: str
    last_name: str
    age: int
    gender: str
    birth_date: date
    email: EmailStr
    address: str
    city: str
    province: str
    state: str
    zip_code: str
    country: str
    phone_number: str

class CustomerCreate(CustomerBase):
    pass  # Uguale a CustomerBase, nessun campo extra

class CustomerUpdate(CustomerBase):
    pass  # Uguale a CustomerBase, nessun campo extra

class CustomerResponse(CustomerBase):
    id: int  # Aggiunge l'ID nel modello di risposta

    class Config:
        from_attributes = True
