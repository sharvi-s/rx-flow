import asyncio
import os
from typing import Any

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


app = FastAPI(
    title="RxFlow Verification Service",
    description="FastAPI service for insurance verification, RxNorm medication search, and Claude explanations.",
    version="0.1.0",
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8050").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClaimVerificationRequest(BaseModel):
    patient_name: str = Field(min_length=1)
    insurance_provider: str = Field(min_length=1)
    medication: str = Field(min_length=1)
    amount: float = Field(ge=0)


class ClaimExplanationRequest(ClaimVerificationRequest):
    anomaly_reason: str | None = None
    verification_status: str | None = None
    verification_sources: list[str] = Field(default_factory=list)


async def _check_payer_directory(insurance_provider: str) -> str | None:
    """NPI Registry: verify the payer is a registered healthcare organization."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://npiregistry.cms.hhs.gov/api/",
                params={"version": "2.1", "organization_name": insurance_provider,
                        "enumeration_type": "NPI-2", "limit": 1},
            )
            resp.raise_for_status()
            if resp.json().get("result_count", 0) > 0:
                return None
    except Exception:
        # Fallback: accept known major payers when NPI is unreachable
        known = ("aetna", "blue cross", "cigna", "humana", "medicare", "medicaid", "united", "optum", "anthem")
        if any(name in insurance_provider.lower() for name in known):
            return None
    return "Insurance provider was not found in the NPI payer directory."


async def _check_formulary_rules(medication: str, amount: float) -> str | None:
    """RxNorm: confirm the drug exists and flag specialty medications needing prior auth."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://rxnav.nlm.nih.gov/REST/rxcui.json",
                params={"name": medication, "search": 1},
            )
            resp.raise_for_status()
            ids = resp.json().get("idGroup", {}).get("rxnormId") or []
            if not ids:
                return "Medication not recognized in the RxNorm drug database."
    except Exception:
        pass  # Don't penalize on transient API failure

    specialty_terms = ("humira", "enbrel", "stelara", "ozempic", "wegovy", "mounjaro")
    if any(t in medication.lower() for t in specialty_terms) and amount > 750:
        return "Specialty medication requires formulary and prior authorization review."
    return None


async def _check_historical_risk(medication: str, amount: float) -> str | None:
    """OpenFDA adverse events: high report volume signals elevated claim risk."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                "https://api.fda.gov/drug/event.json",
                params={"search": f'patient.drug.medicinalproduct:"{medication}"', "limit": 1},
            )
            if resp.status_code == 200:
                total = resp.json().get("meta", {}).get("results", {}).get("total", 0)
                if total > 10_000:
                    return f"Medication has {total:,} FDA adverse event reports — elevated risk profile."
    except Exception:
        pass

    if amount > 1000:
        return "Claim amount exceeds the automated high-value threshold."
    return None


async def verify_against_sources(claim: ClaimVerificationRequest) -> dict[str, Any]:
    payer_flag, drug_flag, risk_flag = await asyncio.gather(
        _check_payer_directory(claim.insurance_provider),
        _check_formulary_rules(claim.medication, claim.amount),
        _check_historical_risk(claim.medication, claim.amount),
    )
    flags = [f for f in [payer_flag, drug_flag, risk_flag] if f]
    return {
        "verification_status": "verified" if not flags else "review_required",
        "verification_sources": ["payer-directory", "formulary-rules", "historical-claim-risk"],
        "flags": flags,
        "anomaly_flag": bool(flags),
        "anomaly_reason": " ".join(flags) if flags else None,
    }


async def fetch_rxnorm(query: str) -> list[dict[str, str]]:
    url = "https://rxnav.nlm.nih.gov/REST/drugs.json"
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.get(url, params={"name": query})
        response.raise_for_status()
        data = response.json()

    concepts: list[dict[str, str]] = []
    groups = data.get("drugGroup", {}).get("conceptGroup", [])
    for group in groups:
        for concept in group.get("conceptProperties", []) or []:
            concepts.append(
                {
                    "rxcui": concept.get("rxcui", ""),
                    "name": concept.get("name", ""),
                    "synonym": concept.get("synonym", ""),
                    "tty": concept.get("tty", ""),
                }
            )
    return concepts[:12]


def fallback_explanation(claim: ClaimExplanationRequest) -> str:
    reason = claim.anomaly_reason or "the insurance verification rules requested review"
    return (
        f"This claim was flagged because {reason} "
        f"The pharmacist should confirm payer eligibility, formulary status, and whether the ${claim.amount:.2f} amount "
        "matches the expected reimbursement range before approving."
    )


async def generate_claude_explanation(claim: ClaimExplanationRequest) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-test"):
        return fallback_explanation(claim)

    prompt = (
        "You are a pharmacy claims analyst. Explain in 2-3 plain-language sentences why this claim was flagged "
        "and what a pharmacist should check.\n\n"
        f"Patient: {claim.patient_name}\n"
        f"Medication: {claim.medication}\n"
        f"Insurance Provider: {claim.insurance_provider}\n"
        f"Amount: ${claim.amount:.2f}\n"
        f"Verification Status: {claim.verification_status or 'unknown'}\n"
        f"Verification Sources: {', '.join(claim.verification_sources)}\n"
        f"Anomaly Reason: {claim.anomaly_reason or 'Not provided'}"
    )
    payload = {
        "model": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
        "max_tokens": 220,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    content = data.get("content", [])
    if content and isinstance(content, list):
        return content[0].get("text", fallback_explanation(claim))
    return fallback_explanation(claim)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/medications/search")
async def search_medications(query: str = Query(..., min_length=2)) -> dict[str, Any]:
    return {"query": query, "results": await fetch_rxnorm(query)}


@app.post("/api/v1/insurance/verify")
async def verify_insurance(claim: ClaimVerificationRequest) -> dict[str, Any]:
    return await verify_against_sources(claim)


@app.post("/api/v1/ai/explain")
async def explain_claim(claim: ClaimExplanationRequest) -> dict[str, str]:
    return {"explanation": await generate_claude_explanation(claim)}
