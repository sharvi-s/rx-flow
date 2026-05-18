"""
RxFlow — Claim service layer
Business logic lives here, not in the route handlers.
"""
import uuid
import random
import string
from datetime import datetime, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.models import Claim, ClaimStatus, Patient, Drug, Payer, AuditLog
from app.schemas.schemas import ClaimCreate, ClaimUpdate, ClaimStats


def _generate_claim_number() -> str:
    """CLM-YYYYMMDD-XXXX"""
    suffix = "".join(random.choices(string.digits, k=4))
    return f"CLM-{datetime.utcnow().strftime('%Y%m%d')}-{suffix}"


# ─── VALIDATION ───────────────────────────────────────────────────────────────
VALIDATION_CHECKS = [
    ("NULL_CHECK",     lambda c: c.claim_amount is not None and c.qty_dispensed is not None),
    ("AMOUNT_RANGE",   lambda c: 0 < c.claim_amount < 10_000),
    ("QTY_RANGE",      lambda c: 0 < c.qty_dispensed <= 1000),
    ("DAYS_SUPPLY",    lambda c: 0 < c.days_supply <= 365),
    ("FILL_DATE",      lambda c: c.fill_date <= date.today()),
    ("COPAY_RANGE",    lambda c: 0 <= c.copay <= c.claim_amount),
    ("REFILL_ORDER",   lambda c: c.refill_number <= c.refills_auth),
]

def validate_claim(claim: Claim) -> tuple[bool, list[str]]:
    """Run all validation checks. Returns (passed, list_of_failures)."""
    failures = []
    for name, check in VALIDATION_CHECKS:
        try:
            if not check(claim):
                failures.append(name)
        except Exception:
            failures.append(name)
    return len(failures) == 0, failures


# ─── AI ANOMALY FLAG ──────────────────────────────────────────────────────────
def ai_anomaly_check(claim: Claim) -> tuple[bool, Optional[str]]:
    """
    Heuristic anomaly detection. In production this calls Claude API.
    Returns (flagged, reason).
    """
    flags = []

    if claim.claim_amount > 500:
        flags.append(f"Unusually high claim amount (${claim.claim_amount:.2f})")

    if claim.days_supply > 90:
        flags.append(f"Days supply ({claim.days_supply}) exceeds standard 90-day limit")

    if claim.qty_dispensed > 360:
        flags.append(f"High quantity dispensed ({claim.qty_dispensed} units)")

    if claim.copay == 0 and claim.claim_amount > 100:
        flags.append("Zero copay on high-value claim — verify payer contract")

    if claim.refill_number > claim.refills_auth:
        flags.append(f"Refill #{claim.refill_number} exceeds authorized refills ({claim.refills_auth})")

    flagged = len(flags) > 0
    reason  = "; ".join(flags) if flags else None
    return flagged, reason


# ─── CRUD ─────────────────────────────────────────────────────────────────────
async def create_claim(db: AsyncSession, data: ClaimCreate) -> Claim:
    claim = Claim(
        **data.model_dump(),
        claim_number=_generate_claim_number(),
        status=ClaimStatus.pending,
    )

    # run validation
    passed, failures = validate_claim(claim)
    if not passed:
        claim.status = ClaimStatus.rejected
        claim.rejection_code = "VALIDATION"
        claim.rejection_reason = f"Failed checks: {', '.join(failures)}"
    else:
        claim.status = ClaimStatus.processing

    # run AI anomaly check
    flagged, reason = ai_anomaly_check(claim)
    claim.ai_flag = flagged
    claim.ai_flag_reason = reason

    db.add(claim)

    # audit log
    db.add(AuditLog(
        table_name="claims",
        record_id=claim.id,
        action="INSERT",
        changed_by=data.created_by,
        new_data={"claim_number": claim.claim_number, "status": claim.status.value},
    ))

    await db.commit()
    await db.refresh(claim)
    return claim


async def get_claim(db: AsyncSession, claim_id: uuid.UUID) -> Optional[Claim]:
    result = await db.execute(
        select(Claim)
        .options(
            selectinload(Claim.patient).selectinload(Patient.payer),
            selectinload(Claim.drug),
            selectinload(Claim.payer),
        )
        .where(Claim.id == claim_id)
    )
    return result.scalar_one_or_none()


async def list_claims(
    db:       AsyncSession,
    page:     int = 1,
    size:     int = 20,
    status:   Optional[ClaimStatus] = None,
    patient_id: Optional[uuid.UUID] = None,
) -> tuple[list[Claim], int]:
    q = select(Claim).options(
        selectinload(Claim.patient),
        selectinload(Claim.drug),
        selectinload(Claim.payer),
    )

    filters = []
    if status:
        filters.append(Claim.status == status)
    if patient_id:
        filters.append(Claim.patient_id == patient_id)
    if filters:
        q = q.where(and_(*filters))

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.order_by(Claim.submitted_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(q)
    return result.scalars().all(), total


async def update_claim(
    db: AsyncSession, claim_id: uuid.UUID, data: ClaimUpdate, changed_by: str = None
) -> Optional[Claim]:
    claim = await get_claim(db, claim_id)
    if not claim:
        return None

    old_status = claim.status.value
    update_dict = data.model_dump(exclude_none=True)

    for field, value in update_dict.items():
        setattr(claim, field, value)

    if data.status in (ClaimStatus.approved, ClaimStatus.rejected):
        claim.processed_at = datetime.utcnow()

    db.add(AuditLog(
        table_name="claims",
        record_id=claim_id,
        action="UPDATE",
        changed_by=changed_by,
        old_data={"status": old_status},
        new_data=update_dict,
    ))

    await db.commit()
    await db.refresh(claim)
    return claim


async def get_stats(db: AsyncSession) -> ClaimStats:
    result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(func.cast(Claim.status == ClaimStatus.approved,  "int")).label("approved"),
            func.sum(func.cast(Claim.status == ClaimStatus.pending,    "int")).label("pending"),
            func.sum(func.cast(Claim.status == ClaimStatus.rejected,   "int")).label("rejected"),
            func.sum(func.cast(Claim.status == ClaimStatus.processing, "int")).label("processing"),
            func.coalesce(func.sum(Claim.claim_amount), 0).label("total_revenue"),
        )
    )
    row = result.one()
    total = row.total or 0
    approved = row.approved or 0
    return ClaimStats(
        total=total,
        approved=approved,
        pending=row.pending or 0,
        rejected=row.rejected or 0,
        processing=row.processing or 0,
        total_revenue=float(row.total_revenue or 0),
        approval_rate=round(approved / total * 100, 1) if total > 0 else 0.0,
    )
