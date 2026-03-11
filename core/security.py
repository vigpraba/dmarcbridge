from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer
from config import settings
from fastapi import Request, HTTPException, status

# ─── Password Hashing ────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ─── Session Cookie ──────────────────────────────────────
serializer = URLSafeTimedSerializer(settings.SESSION_SECRET_KEY)

def create_session_cookie(user_id: str) -> str:
    return serializer.dumps(user_id)

def verify_session_cookie(token: str) -> str:
    try:
        user_id = serializer.loads(token, max_age=86400)  # 24 hours
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

# ─── Get Current User From Cookie ────────────────────────
def get_current_user_id(request: Request) -> str:
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return verify_session_cookie(token)
