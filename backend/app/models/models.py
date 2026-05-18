"""
RxFlow — SQLAlchemy ORM models
"""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Boolean, Numeric, SmallInteger, Date,
    ForeignKey, Text, TIMESTAMP, Enum as SAEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
import enum


class ClaimStatus(str, enum.Enum):
    draft      = "draft"
    pending    = "pending"
    processing = "processing"
    approved   = "approved"
    rejected   = "rejected"
    reversed   = "reversed"


class Payer(Base):
    __tablename__ = "payers"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:       Mapped[str]       = mapped_column(String(120), unique=True, nullable=False)
    bin:        Mapped[Optional[str]] = mapped_column(String(10))
    pcn:        Mapped[Optional[str]] = mapped_column(String(20))
    phone:      Mapped[Optional[str]] = mapped_column(String(20))
    active:     Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    patients: Mapped[list["Patient"]] = relationship(back_populates="payer")
    claims:   Mapped[list["Claim"]]   = relationship(back_populates="payer")


class Patient(Base):
    __tablename__ = "patients"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str]       = mapped_column(String(80), nullable=False)
    last_name:  Mapped[str]       = mapped_column(String(80), nullable=False)
    dob:        Mapped[date]      = mapped_column(Date, nullable=False)
    member_id:  Mapped[str]       = mapped_column(String(40), unique=True, nullable=False)
    payer_id:   Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("payers.id"))
    allergies:  Mapped[Optional[str]] = mapped_column(Text)
    notes:      Mapped[Optional[str]] = mapped_column(Text)
    active:     Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    payer:  Mapped[Optional["Payer"]]  = relationship(back_populates="patients")
    claims: Mapped[list["Claim"]]      = relationship(back_populates="patient")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Prescriber(Base):
    __tablename__ = "prescribers"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    npi:        Mapped[str]       = mapped_column(String(10), unique=True, nullable=False)
    first_name: Mapped[str]       = mapped_column(String(80), nullable=False)
    last_name:  Mapped[str]       = mapped_column(String(80), nullable=False)
    specialty:  Mapped[Optional[str]] = mapped_column(String(100))
    phone:      Mapped[Optional[str]] = mapped_column(String(20))
    fax:        Mapped[Optional[str]] = mapped_column(String(20))
    active:     Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    claims: Mapped[list["Claim"]] = relationship(back_populates="prescriber")


class Drug(Base):
    __tablename__ = "drugs"

    id:           Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ndc:          Mapped[str]       = mapped_column(String(11), unique=True, nullable=False)
    name:         Mapped[str]       = mapped_column(String(200), nullable=False)
    strength:     Mapped[Optional[str]] = mapped_column(String(50))
    form:         Mapped[Optional[str]] = mapped_column(String(50))
    unit_cost:    Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    requires_pa:  Mapped[bool]      = mapped_column(Boolean, default=False)
    controlled:   Mapped[bool]      = mapped_column(Boolean, default=False)
    schedule:     Mapped[Optional[int]] = mapped_column(SmallInteger)
    active:       Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at:   Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    claims: Mapped[list["Claim"]] = relationship(back_populates="drug")


class Claim(Base):
    __tablename__ = "claims"

    id:              Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_number:    Mapped[str]        = mapped_column(String(20), unique=True, nullable=False)
    patient_id:      Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    prescriber_id:   Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("prescribers.id"))
    drug_id:         Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("drugs.id"), nullable=False)
    payer_id:        Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("payers.id"), nullable=False)

    qty_dispensed:   Mapped[float]      = mapped_column(Numeric(10, 3), nullable=False)
    days_supply:     Mapped[int]        = mapped_column(SmallInteger, nullable=False)
    refills_auth:    Mapped[int]        = mapped_column(SmallInteger, default=0)
    refill_number:   Mapped[int]        = mapped_column(SmallInteger, default=0)
    fill_date:       Mapped[date]       = mapped_column(Date, nullable=False)
    written_date:    Mapped[Optional[date]] = mapped_column(Date)

    claim_amount:    Mapped[float]      = mapped_column(Numeric(10, 2), nullable=False)
    copay:           Mapped[float]      = mapped_column(Numeric(10, 2), default=0)
    plan_pays:       Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    dispensing_fee:  Mapped[Optional[float]] = mapped_column(Numeric(10, 2))

    status:          Mapped[ClaimStatus] = mapped_column(SAEnum(ClaimStatus), default=ClaimStatus.pending)
    rejection_code:  Mapped[Optional[str]] = mapped_column(String(10))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    ai_flag:         Mapped[bool]       = mapped_column(Boolean, default=False)
    ai_flag_reason:  Mapped[Optional[str]] = mapped_column(Text)

    submitted_at:    Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    processed_at:    Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_by:      Mapped[Optional[str]] = mapped_column(String(80))
    updated_at:      Mapped[datetime]   = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    patient:    Mapped["Patient"]           = relationship(back_populates="claims")
    prescriber: Mapped[Optional["Prescriber"]] = relationship(back_populates="claims")
    drug:       Mapped["Drug"]              = relationship(back_populates="claims")
    payer:      Mapped["Payer"]             = relationship(back_populates="claims")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id:         Mapped[int]       = mapped_column(primary_key=True, autoincrement=True)
    table_name: Mapped[str]       = mapped_column(String(50), nullable=False)
    record_id:  Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action:     Mapped[str]       = mapped_column(String(10), nullable=False)
    changed_by: Mapped[Optional[str]] = mapped_column(String(80))
    changed_at: Mapped[datetime]  = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    old_data:   Mapped[Optional[dict]] = mapped_column(JSON)
    new_data:   Mapped[Optional[dict]] = mapped_column(JSON)
