from pydantic import BaseModel,ConfigDict
from typing import Optional

class Token(BaseModel):
    """
    Schema for JWT token response
    """
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """
    Schema for JWT token payload
    """
    sub: Optional[int] = None
    token_type: Optional[str] = None  # "access" or "refresh"
    exp: Optional[int] = None