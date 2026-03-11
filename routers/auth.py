from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import Contact, GoogleAccount, ContactStatus
from schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    GoogleAuthURL, GoogleCallbackResponse,
    UserResponse
)
from core.security import hash_password, verify_password, create_session_cookie, get_current_user_id
from core.oauth import get_google_auth_url, get_google_user_info, create_jwt_token
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])

# ─── Email/Password Register ─────────────────────────────
@router.post("/register", response_model=RegisterResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(Contact).where(Contact.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    contact = Contact(
        id=uuid.uuid4(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        status=ContactStatus.pending_verification
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact

# ─── Email/Password Login ────────────────────────────────
@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.email == payload.email))
    contact = result.scalar_one_or_none()

    if not contact or not contact.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, contact.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Set HttpOnly session cookie
    session_token = create_session_cookie(str(contact.id))
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=False,    # Set True in production (HTTPS)
        samesite="lax",
        max_age=86400    # 24 hours
    )
    return {"message": "Login successful", "email": contact.email}

# ─── Logout ──────────────────────────────────────────────
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("session")
    return {"message": "Logged out successfully"}

# ─── Google OAuth - Get Auth URL ─────────────────────────
@router.get("/google")
async def google_login():
    from fastapi.responses import RedirectResponse
    url = await get_google_auth_url()
    return RedirectResponse(url=url)

# ─── Google OAuth - Callback ─────────────────────────────
@router.get("/google/callback")
async def google_callback(code: str, response: Response, db: AsyncSession = Depends(get_db)):
    user_info = await get_google_user_info(code)

    google_sub = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name")

    # Check if google account already exists
    result = await db.execute(select(GoogleAccount).where(GoogleAccount.google_sub == google_sub))
    google_account = result.scalar_one_or_none()

    if google_account:
        contact_id = str(google_account.contact_id)
    else:
        # Check if contact with this email exists
        result = await db.execute(select(Contact).where(Contact.email == email))
        contact = result.scalar_one_or_none()

        if not contact:
            contact = Contact(
                id=uuid.uuid4(),
                email=email,
                name=name,
                email_verified=True,
                status=ContactStatus.active
            )
            db.add(contact)
            await db.flush()

        google_account = GoogleAccount(
            id=uuid.uuid4(),
            contact_id=contact.id,
            google_sub=google_sub,
            email=email
        )
        db.add(google_account)
        await db.commit()
        contact_id = str(contact.id)

    # Set session cookie and redirect to dashboard
    from fastapi.responses import RedirectResponse
    session_token = create_session_cookie(contact_id)
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400
    )
    return redirect

# ─── Get Current User ────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user_id(request)
    result = await db.execute(select(Contact).where(Contact.id == uuid.UUID(user_id)))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="User not found")
    return contact
