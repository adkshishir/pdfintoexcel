from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminMeResponse(BaseModel):
    id: str
    email: str
    roles: list[str]
