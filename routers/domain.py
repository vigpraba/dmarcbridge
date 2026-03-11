import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.domain import Domain, DomainCheck
from core.security import get_current_user_id
from core.dns_utils import verify_domain_token, get_dns_health
from pydantic import BaseModel

router = APIRouter(prefix="/domains", tags=["domains"])

class AddDomainRequest(BaseModel):
    domain_name: str

# ─── Step 1: Add Domain ──────────────────────────────────
@router.post("/")
async def add_domain(payload: AddDomainRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user_id(request)

    # Check if domain already exists for this user
    result = await db.execute(
        select(Domain).where(
            Domain.contact_id == uuid.UUID(user_id),
            Domain.domain_name == payload.domain_name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain already added")

    token = f"dmarcbridge-verify={secrets.token_hex(16)}"
    domain = Domain(
        id=uuid.uuid4(),
        contact_id=uuid.UUID(user_id),
        domain_name=payload.domain_name,
        verification_token=token,
        is_verified=False
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)

    return {
        "id": str(domain.id),
        "domain_name": domain.domain_name,
        "verification_token": token,
        "is_verified": False
    }

# ─── Step 2: Verify Domain Ownership ────────────────────
@router.post("/{domain_id}/verify")
async def verify_domain(domain_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.contact_id == uuid.UUID(user_id)
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    verified = verify_domain_token(domain.domain_name, domain.verification_token)
    if verified:
        domain.is_verified = True
        await db.commit()

    return {"is_verified": verified}

# ─── Step 3: Check DNS Records ───────────────────────────
@router.post("/{domain_id}/check")
async def check_dns(domain_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user_id(request)

    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.contact_id == uuid.UUID(user_id)
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    health = get_dns_health(domain.domain_name)

    check = DomainCheck(
        id=uuid.uuid4(),
        domain_id=domain.id,
        spf_record=health["spf"]["record"],
        dkim_record=health["dkim"]["record"],
        dmarc_record=health["dmarc"]["record"],
        spf_status=health["spf"]["status"],
        dkim_status=health["dkim"]["status"],
        dmarc_status=health["dmarc"]["status"],
    )
    db.add(check)
    await db.commit()

    return health

# ─── Get All Domains ─────────────────────────────────────
@router.get("/")
async def get_domains(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_current_user_id(request)
    result = await db.execute(
        select(Domain).where(Domain.contact_id == uuid.UUID(user_id))
    )
    domains = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "domain_name": d.domain_name,
            "is_verified": d.is_verified,
            "created_at": str(d.created_at)
        }
        for d in domains
    ]
