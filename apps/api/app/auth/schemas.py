from pydantic import Field

from app.schemas import CamelModel


class UserRead(CamelModel):
    id: str
    email: str


class RegisterRequest(CamelModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(CamelModel):
    email: str
    password: str


class AuthResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
