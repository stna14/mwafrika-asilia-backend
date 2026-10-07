import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if len(v) > 128:
        raise ValueError("Password must be at most 128 characters")
    if not re.search(r"[A-Za-z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


class AdminLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AdminCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Full name cannot be empty")
        return v

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut