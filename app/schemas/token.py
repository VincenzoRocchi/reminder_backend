from pydantic import BaseModel


class Token(BaseModel):
    """
    Schema for JWT token response
    """
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """
    Schema for JWT token payload
    """
    sub: int = None