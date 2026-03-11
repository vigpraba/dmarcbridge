import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base

class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"))
    domain_name: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_token: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    checks: Mapped[list["DomainCheck"]] = relationship("DomainCheck", back_populates="domain")

class DomainCheck(Base):
    __tablename__ = "domain_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"))
    spf_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    dkim_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    dmarc_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    spf_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dkim_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dmarc_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    domain: Mapped["Domain"] = relationship("Domain", back_populates="checks")
