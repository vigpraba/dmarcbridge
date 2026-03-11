from authlib.integrations.httpx_client import AsyncOAuth2Client
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config import settings
import httpx

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# ─── Build Google Auth URL ───────────────────────────────
async def get_google_auth_url() -> str:
    async with AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
        scope="openid email profile"
    ) as client:
        async with httpx.AsyncClient() as http:
            discovery = (await http.get(GOOGLE_DISCOVERY_URL)).json()
        auth_url, _ = client.create_authorization_url(
            discovery["authorization_endpoint"]
        )
        return auth_url

# ─── Exchange Code for User Info ─────────────────────────
async def get_google_user_info(code: str) -> dict:
    async with httpx.AsyncClient() as http:
        discovery = (await http.get(GOOGLE_DISCOVERY_URL)).json()

    async with AsyncOAuth2Client(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    ) as client:
        token = await client.fetch_token(
            discovery["token_endpoint"],
            code=code
        )
        userinfo = await client.get(discovery["userinfo_endpoint"])
        return userinfo.json()

# ─── Issue Your Own JWT ──────────────────────────────────
def create_jwt_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# ─── Verify JWT ──────────────────────────────────────────
def verify_jwt_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise ValueError("Invalid or expired token")
