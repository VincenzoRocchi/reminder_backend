from sqlalchemy import Column, Integer, String, Date
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    last_name = Column(String, index=True)
    age = Column(Integer)
    gender = Column(String)
    birth_date = Column(Date)
    email = Column(String, unique=True, index=True)
    address = Column(String)
    city = Column(String)
    province = Column(String)
    state = Column(String)
    zip_code = Column(String)
    country = Column(String)
    phone_number = Column(String)
    
    def __str__(self):
        return f"Customer: {self.name} {self.last_name}"
    
    def __repr__(self):
        return f"<Customer id={self.id} name='{self.name} {self.last_name}' email='{self.email}'>"