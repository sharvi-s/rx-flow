"""
RxFlow — FastAPI route handlers
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Claim, Patient, Drug, Payer, Prescriber, ClaimStatus
from app.schemas.schemas import (
    ClaimCreate, ClaimOut, ClaimUpdate, PaginatedClaims, ClaimStats,
    PatientCreate, PatientOut, PatientUpdate,
    DrugCreate, DrugOut,
    PayerCreate, PayerOut,
    PrescriberCreate, PrescriberOut,
    AIFlagRequest, AIFlagResponse,
)
from app.services import claim_service

router = APIRouter()


# ─── HEALTH ───────────────────────────────────────────────────────────────────
@router.get("/health")
async def health():
    return {"status": "ok", "service": "RxFlow API"}


# ─── CLAIMS ───────────────────────────────────────────────────────────────────
@router.post("/claims", response_model=ClaimOut, status_code=201, tags=["Claims"])
async def submit_claim(data: ClaimCreate, db: AsyncSession = Depends(get_db)):
    """Submit a new insurance claim. Runs 7 validation checks + AI anomaly detection."""
    return await claim_service.create_claim(db, data)


@router.get("/claims", response_model=PaginatedClaims, tags=["Claims"])
async def list_claims(
    page:       int                    = Query(1, ge=1),
    size:       int                    = Query(20, ge=1, le=100),
    status:     Optional[ClaimStatus]  = Query(None),
    patient_id: Optional[uuid.UUID]    = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List claims with pagination, optional status/patient filter."""
    items, total = await claim_service.list_claims(db, page, size, status, patient_id)
    return PaginatedClaims(total=total, page=page, size=size, items=items)


@router.get("/claims/stats", response_model=ClaimStats, tags=["Claims"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Dashboard stats: totals, approval rate, revenue."""
    return await claim_service.get_stats(db)


@router.get("/claims/{claim_id}", response_model=ClaimOut, tags=["Claims"])
async def get_claim(claim_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    claim = await claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(404, detail="Claim not found")
    return claim


@router.patch("/claims/{claim_id}", response_model=ClaimOut, tags=["Claims"])
async def update_claim(
    claim_id: uuid.UUID,
    data:     ClaimUpdate,
    db:       AsyncSession = Depends(get_db),
):
    """Update claim status, rejection code, plan pays, or AI flag."""
    claim = await claim_service.update_claim(db, claim_id, data)
    if not claim:
        raise HTTPException(404, detail="Claim not found")
    return claim


@router.post("/claims/ai-flag", response_model=AIFlagResponse, tags=["Claims", "AI"])
async def ai_flag_claim(data: AIFlagRequest, db: AsyncSession = Depends(get_db)):
    """Run AI anomaly detection on a specific claim."""
    claim = await claim_service.get_claim(db, data.claim_id)
    if not claim:
        raise HTTPException(404, detail="Claim not found")
    flagged, reason = claim_service.ai_anomaly_check(claim)
    return AIFlagResponse(
        claim_id=data.claim_id,
        flagged=flagged,
        reason=reason,
        confidence="heuristic" if flagged else None,
    )


# ─── PATIENTS ─────────────────────────────────────────────────────────────────
@router.post("/patients", response_model=PatientOut, status_code=201, tags=["Patients"])
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = Patient(**data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/patients", response_model=list[PatientOut], tags=["Patients"])
async def list_patients(
    q:    Optional[str] = Query(None, description="Search by name or member ID"),
    db:   AsyncSession  = Depends(get_db),
):
    stmt = select(Patient).where(Patient.active == True)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Patient.last_name.ilike(like)
            | Patient.first_name.ilike(like)
            | Patient.member_id.ilike(like)
        )
    result = await db.execute(stmt.limit(100))
    return result.scalars().all()


@router.get("/patients/{patient_id}", response_model=PatientOut, tags=["Patients"])
async def get_patient(patient_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, detail="Patient not found")
    return patient


@router.patch("/patients/{patient_id}", response_model=PatientOut, tags=["Patients"])
async def update_patient(
    patient_id: uuid.UUID, data: PatientUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, detail="Patient not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return patient


# ─── DRUGS ────────────────────────────────────────────────────────────────────
@router.post("/drugs", response_model=DrugOut, status_code=201, tags=["Drugs"])
async def create_drug(data: DrugCreate, db: AsyncSession = Depends(get_db)):
    drug = Drug(**data.model_dump())
    db.add(drug)
    await db.commit()
    await db.refresh(drug)
    return drug


@router.get("/drugs", response_model=list[DrugOut], tags=["Drugs"])
async def list_drugs(
    q:  Optional[str] = Query(None, description="Search by name or NDC"),
    db: AsyncSession  = Depends(get_db),
):
    stmt = select(Drug).where(Drug.active == True)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Drug.name.ilike(like) | Drug.ndc.ilike(like))
    result = await db.execute(stmt.limit(200))
    return result.scalars().all()


# ─── PAYERS ───────────────────────────────────────────────────────────────────
@router.get("/payers", response_model=list[PayerOut], tags=["Payers"])
async def list_payers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payer).where(Payer.active == True))
    return result.scalars().all()


# ─── PRESCRIBERS ──────────────────────────────────────────────────────────────
@router.post("/prescribers", response_model=PrescriberOut, status_code=201, tags=["Prescribers"])
async def create_prescriber(data: PrescriberCreate, db: AsyncSession = Depends(get_db)):
    prescriber = Prescriber(**data.model_dump())
    db.add(prescriber)
    await db.commit()
    await db.refresh(prescriber)
    return prescriber


@router.get("/prescribers", response_model=list[PrescriberOut], tags=["Prescribers"])
async def list_prescribers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prescriber).where(Prescriber.active == True))
    return result.scalars().all()
