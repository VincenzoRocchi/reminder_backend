from typing import Optional
from pydantic import BaseModel

class TokenData(BaseModel):
    sub: Optional[str] = None

class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    token: str
    new_password: str