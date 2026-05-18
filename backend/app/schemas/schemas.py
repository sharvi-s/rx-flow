"""
RxFlow — Pydantic v2 schemas for request/response validation
"""
from __future__ import annotations
import uuid
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.models import ClaimStatus


# ─── PAYER ────────────────────────────────────────────────────────────────────
class PayerBase(BaseModel):
    name:  str
    bin:   Optional[str] = None
    pcn:   Optional[str] = None
    phone: Optional[str] = None

class PayerCreate(PayerBase): pass

class PayerOut(PayerBase):
    id:         uuid.UUID
    active:     bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── PATIENT ──────────────────────────────────────────────────────────────────
class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=80)
    last_name:  str = Field(..., min_length=1, max_length=80)
    dob:        date
    member_id:  str = Field(..., min_length=1, max_length=40)
    payer_id:   Optional[uuid.UUID] = None
    allergies:  Optional[str] = None
    notes:      Optional[str] = None

class PatientCreate(PatientBase): pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    allergies:  Optional[str] = None
    notes:      Optional[str] = None
    payer_id:   Optional[uuid.UUID] = None
    active:     Optional[bool] = None

class PatientOut(PatientBase):
    id:         uuid.UUID
    active:     bool
    created_at: datetime
    updated_at: datetime
    payer:      Optional[PayerOut] = None
    model_config = {"from_attributes": True}


# ─── PRESCRIBER ───────────────────────────────────────────────────────────────
class PrescriberBase(BaseModel):
    npi:       str = Field(..., min_length=10, max_length=10)
    first_name: str
    last_name:  str
    specialty:  Optional[str] = None
    phone:      Optional[str] = None
    fax:        Optional[str] = None

class PrescriberCreate(PrescriberBase): pass

class PrescriberOut(PrescriberBase):
    id:         uuid.UUID
    active:     bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── DRUG ─────────────────────────────────────────────────────────────────────
class DrugBase(BaseModel):
    ndc:         str = Field(..., min_length=11, max_length=11)
    name:        str
    strength:    Optional[str] = None
    form:        Optional[str] = None
    unit_cost:   Optional[float] = None
    requires_pa: bool = False
    controlled:  bool = False
    schedule:    Optional[int] = Field(None, ge=2, le=5)

class DrugCreate(DrugBase): pass

class DrugOut(DrugBase):
    id:         uuid.UUID
    active:     bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── CLAIM ────────────────────────────────────────────────────────────────────
class ClaimBase(BaseModel):
    patient_id:    uuid.UUID
    prescriber_id: Optional[uuid.UUID] = None
    drug_id:       uuid.UUID
    payer_id:      uuid.UUID
    qty_dispensed: float = Field(..., gt=0)
    days_supply:   int   = Field(..., gt=0, le=365)
    refills_auth:  int   = Field(0, ge=0)
    refill_number: int   = Field(0, ge=0)
    fill_date:     date
    written_date:  Optional[date] = None
    claim_amount:  float = Field(..., gt=0)
    copay:         float = Field(0, ge=0)
    dispensing_fee: Optional[float] = None
    created_by:    Optional[str] = None

    @field_validator("fill_date")
    @classmethod
    def fill_date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Fill date cannot be in the future")
        return v

class ClaimCreate(ClaimBase): pass

class ClaimUpdate(BaseModel):
    status:           Optional[ClaimStatus] = None
    rejection_code:   Optional[str] = None
    rejection_reason: Optional[str] = None
    plan_pays:        Optional[float] = None
    ai_flag:          Optional[bool] = None
    ai_flag_reason:   Optional[str] = None

class ClaimOut(ClaimBase):
    id:               uuid.UUID
    claim_number:     str
    status:           ClaimStatus
    plan_pays:        Optional[float] = None
    rejection_code:   Optional[str] = None
    rejection_reason: Optional[str] = None
    ai_flag:          bool
    ai_flag_reason:   Optional[str] = None
    submitted_at:     datetime
    processed_at:     Optional[datetime] = None
    updated_at:       datetime
    patient:          Optional[PatientOut] = None
    drug:             Optional[DrugOut] = None
    payer:            Optional[PayerOut] = None
    model_config = {"from_attributes": True}


# ─── PAGINATION ───────────────────────────────────────────────────────────────
class PaginatedClaims(BaseModel):
    total:  int
    page:   int
    size:   int
    items:  list[ClaimOut]

class ClaimStats(BaseModel):
    total:      int
    approved:   int
    pending:    int
    rejected:   int
    processing: int
    total_revenue: float
    approval_rate: float


# ─── AI FLAG ──────────────────────────────────────────────────────────────────
class AIFlagRequest(BaseModel):
    claim_id: uuid.UUID

class AIFlagResponse(BaseModel):
    claim_id:   uuid.UUID
    flagged:    bool
    reason:     Optional[str]
    confidence: Optional[str]
