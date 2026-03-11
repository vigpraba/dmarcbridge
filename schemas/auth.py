from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from models.user import ContactStatus

# ─── Register ───────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class RegisterResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    status: ContactStatus

    class Config:
        from_attributes = True

# ─── Login ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    message: str
    email: str

# ─── Google OAuth ────────────────────────────────────────
class GoogleAuthURL(BaseModel):
    url: str

class GoogleCallbackResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ─── Current User ────────────────────────────────────────
class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None
    email_verified: bool
    status: ContactStatus
    created_at: datetime

    class Config:
        from_attributes = True
