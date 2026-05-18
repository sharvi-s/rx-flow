"""
RxFlow — test suite
Run: pytest backend/tests/ -v
"""
import pytest
from datetime import date
from app.models.models import Claim, ClaimStatus
from app.services.claim_service import validate_claim, ai_anomaly_check, _generate_claim_number


def make_claim(**kwargs) -> Claim:
    defaults = dict(
        claim_amount=25.00,
        qty_dispensed=90,
        days_supply=90,
        copay=5.00,
        refills_auth=3,
        refill_number=1,
        fill_date=date.today(),
        status=ClaimStatus.pending,
        ai_flag=False,
    )
    defaults.update(kwargs)
    return Claim(**defaults)


# ─── VALIDATION TESTS ─────────────────────────────────────────────────────────
class TestValidation:

    def test_valid_claim_passes_all_checks(self):
        claim = make_claim()
        passed, failures = validate_claim(claim)
        assert passed is True
        assert failures == []

    def test_zero_claim_amount_fails(self):
        claim = make_claim(claim_amount=0)
        passed, failures = validate_claim(claim)
        assert passed is False
        assert "AMOUNT_RANGE" in failures

    def test_negative_qty_fails(self):
        claim = make_claim(qty_dispensed=-1)
        passed, failures = validate_claim(claim)
        assert passed is False
        assert "QTY_RANGE" in failures

    def test_days_supply_over_365_fails(self):
        claim = make_claim(days_supply=400)
        passed, failures = validate_claim(claim)
        assert passed is False
        assert "DAYS_SUPPLY" in failures

    def test_copay_exceeds_claim_amount_fails(self):
        claim = make_claim(claim_amount=10.00, copay=50.00)
        passed, failures = validate_claim(claim)
        assert passed is False
        assert "COPAY_RANGE" in failures

    def test_refill_exceeds_authorized_fails(self):
        claim = make_claim(refill_number=5, refills_auth=3)
        passed, failures = validate_claim(claim)
        assert passed is False
        assert "REFILL_ORDER" in failures

    def test_extreme_amount_fails(self):
        claim = make_claim(claim_amount=15000)
        passed, failures = validate_claim(claim)
        assert passed is False
        assert "AMOUNT_RANGE" in failures


# ─── AI FLAG TESTS ────────────────────────────────────────────────────────────
class TestAIFlag:

    def test_normal_claim_not_flagged(self):
        claim = make_claim(claim_amount=25.00, copay=5.00, days_supply=30)
        flagged, reason = ai_anomaly_check(claim)
        assert flagged is False
        assert reason is None

    def test_high_amount_flagged(self):
        claim = make_claim(claim_amount=750.00, copay=20.00)
        flagged, reason = ai_anomaly_check(claim)
        assert flagged is True
        assert "high claim amount" in reason.lower()

    def test_long_days_supply_flagged(self):
        claim = make_claim(days_supply=180)
        flagged, reason = ai_anomaly_check(claim)
        assert flagged is True
        assert "Days supply" in reason

    def test_zero_copay_high_value_flagged(self):
        claim = make_claim(claim_amount=200.00, copay=0)
        flagged, reason = ai_anomaly_check(claim)
        assert flagged is True
        assert "copay" in reason.lower()


# ─── CLAIM NUMBER TESTS ───────────────────────────────────────────────────────
class TestClaimNumber:

    def test_claim_number_format(self):
        num = _generate_claim_number()
        assert num.startswith("CLM-")
        parts = num.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8   # YYYYMMDD
        assert len(parts[2]) == 4   # random digits

    def test_claim_numbers_unique(self):
        numbers = {_generate_claim_number() for _ in range(100)}
        assert len(numbers) > 90   # near-certain uniqueness
