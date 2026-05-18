-- RxFlow Database Schema
-- PostgreSQL 15+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── PAYERS ───────────────────────────────────────────────────────────────────
CREATE TABLE payers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(120) NOT NULL UNIQUE,
    bin         VARCHAR(10),
    pcn         VARCHAR(20),
    phone       VARCHAR(20),
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── PATIENTS ─────────────────────────────────────────────────────────────────
CREATE TABLE patients (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name  VARCHAR(80)  NOT NULL,
    last_name   VARCHAR(80)  NOT NULL,
    dob         DATE         NOT NULL,
    member_id   VARCHAR(40)  UNIQUE NOT NULL,
    payer_id    UUID         REFERENCES payers(id),
    allergies   TEXT,
    notes       TEXT,
    active      BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_patients_member_id ON patients(member_id);
CREATE INDEX idx_patients_last_name  ON patients(last_name);

-- ─── PRESCRIBERS ──────────────────────────────────────────────────────────────
CREATE TABLE prescribers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    npi         VARCHAR(10)  UNIQUE NOT NULL,
    first_name  VARCHAR(80)  NOT NULL,
    last_name   VARCHAR(80)  NOT NULL,
    specialty   VARCHAR(100),
    phone       VARCHAR(20),
    fax         VARCHAR(20),
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── DRUGS ────────────────────────────────────────────────────────────────────
CREATE TABLE drugs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ndc             VARCHAR(11)  UNIQUE NOT NULL,
    name            VARCHAR(200) NOT NULL,
    strength        VARCHAR(50),
    form            VARCHAR(50),   -- tablet, capsule, liquid, inhaler
    unit_cost       NUMERIC(10,2),
    requires_pa     BOOLEAN DEFAULT FALSE,  -- prior authorization
    controlled      BOOLEAN DEFAULT FALSE,
    schedule        SMALLINT,              -- DEA schedule 2-5
    active          BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drugs_ndc  ON drugs(ndc);
CREATE INDEX idx_drugs_name ON drugs(name);

-- ─── CLAIMS ───────────────────────────────────────────────────────────────────
CREATE TYPE claim_status AS ENUM (
    'draft', 'pending', 'processing', 'approved', 'rejected', 'reversed'
);

CREATE TABLE claims (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_number    VARCHAR(20)  UNIQUE NOT NULL,
    patient_id      UUID         NOT NULL REFERENCES patients(id),
    prescriber_id   UUID         REFERENCES prescribers(id),
    drug_id         UUID         NOT NULL REFERENCES drugs(id),
    payer_id        UUID         NOT NULL REFERENCES payers(id),

    -- prescription details
    qty_dispensed   NUMERIC(10,3) NOT NULL,
    days_supply     SMALLINT      NOT NULL,
    refills_auth    SMALLINT DEFAULT 0,
    refill_number   SMALLINT DEFAULT 0,
    fill_date       DATE          NOT NULL,
    written_date    DATE,

    -- financials
    claim_amount    NUMERIC(10,2) NOT NULL,
    copay           NUMERIC(10,2) DEFAULT 0,
    plan_pays       NUMERIC(10,2),
    dispensing_fee  NUMERIC(10,2),

    -- status
    status          claim_status  DEFAULT 'pending',
    rejection_code  VARCHAR(10),
    rejection_reason TEXT,
    ai_flag         BOOLEAN DEFAULT FALSE,
    ai_flag_reason  TEXT,

    -- audit
    submitted_at    TIMESTAMPTZ DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    created_by      VARCHAR(80),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_claims_patient_id   ON claims(patient_id);
CREATE INDEX idx_claims_status       ON claims(status);
CREATE INDEX idx_claims_fill_date    ON claims(fill_date);
CREATE INDEX idx_claims_claim_number ON claims(claim_number);

-- ─── AUDIT LOG ────────────────────────────────────────────────────────────────
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    table_name  VARCHAR(50)  NOT NULL,
    record_id   UUID         NOT NULL,
    action      VARCHAR(10)  NOT NULL,  -- INSERT, UPDATE, DELETE
    changed_by  VARCHAR(80),
    changed_at  TIMESTAMPTZ  DEFAULT NOW(),
    old_data    JSONB,
    new_data    JSONB
);

-- ─── AUTO-UPDATE updated_at ───────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_claims_updated_at
    BEFORE UPDATE ON claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── SEED PAYERS ──────────────────────────────────────────────────────────────
INSERT INTO payers (name, bin, pcn) VALUES
    ('Blue Cross Blue Shield', '610415', 'BCBSTX'),
    ('UnitedHealth',           '610011', 'UCARE'),
    ('Aetna',                  '011714', 'AETNA'),
    ('Cigna',                  '610653', 'CIGNA'),
    ('Humana',                 '015581', 'HUMANA'),
    ('Medicare Part D',        '610502', 'MEDD'),
    ('Medicaid Texas',         '000000', 'TXMD'),
    ('Cash Pay',               NULL,     NULL);
