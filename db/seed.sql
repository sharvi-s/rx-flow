-- RxFlow sample data seed
-- Run against a live stack: docker compose exec -T postgres psql -U rxflow -d rxflow < db/seed.sql
-- Safe to re-run (ON CONFLICT DO NOTHING on all inserts)

-- ─── Users ────────────────────────────────────────────────────────────────────
-- password for both accounts: password123
INSERT INTO users (id, name, email, password, role) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'Sarah Kim',    'sarah@rxflow.dev',  '$2b$10$fyQfqPo1VJx/5OlvPoSXou8ZeqNb.jy8vmxca7etHJwl5OWtT7.vC', 'pharmacist'),
  ('a0000000-0000-0000-0000-000000000002', 'Admin User',   'admin@rxflow.dev',  '$2b$10$fyQfqPo1VJx/5OlvPoSXou8ZeqNb.jy8vmxca7etHJwl5OWtT7.vC', 'admin')
ON CONFLICT (id) DO NOTHING;

-- ─── Patients ─────────────────────────────────────────────────────────────────
INSERT INTO patients (id, full_name, date_of_birth, phone) VALUES
  ('b0000000-0000-0000-0000-000000000001', 'James Holloway',   '1965-03-14', '555-0101'),
  ('b0000000-0000-0000-0000-000000000002', 'Maria Santos',     '1978-07-22', '555-0102'),
  ('b0000000-0000-0000-0000-000000000003', 'David Park',       '1990-11-05', '555-0103'),
  ('b0000000-0000-0000-0000-000000000004', 'Linda Foster',     '1955-01-30', '555-0104'),
  ('b0000000-0000-0000-0000-000000000005', 'Carlos Nguyen',    '1983-08-18', '555-0105')
ON CONFLICT (id) DO NOTHING;

-- ─── Payers ───────────────────────────────────────────────────────────────────
INSERT INTO payers (id, name, payer_type, requires_prior_auth) VALUES
  ('c0000000-0000-0000-0000-000000000001', 'Aetna',                  'commercial', false),
  ('c0000000-0000-0000-0000-000000000002', 'Blue Cross Blue Shield',  'commercial', false),
  ('c0000000-0000-0000-0000-000000000003', 'Cigna',                  'commercial', false),
  ('c0000000-0000-0000-0000-000000000004', 'Humana',                 'commercial', true),
  ('c0000000-0000-0000-0000-000000000005', 'Medicare',               'government', false)
ON CONFLICT (id) DO NOTHING;

-- ─── Drugs ────────────────────────────────────────────────────────────────────
INSERT INTO drugs (id, rxcui, name, tty) VALUES
  ('e0000000-0000-0000-0000-000000000001', '29046',   'Lisinopril',    'IN'),
  ('e0000000-0000-0000-0000-000000000002', '6809',    'Metformin',     'IN'),
  ('e0000000-0000-0000-0000-000000000003', '83367',   'Atorvastatin',  'IN'),
  ('e0000000-0000-0000-0000-000000000004', '2200561', 'Ozempic',       'BN'),
  ('e0000000-0000-0000-0000-000000000005', '723',     'Amoxicillin',   'IN'),
  ('e0000000-0000-0000-0000-000000000006', '2395494', 'Wegovy',        'BN'),
  ('e0000000-0000-0000-0000-000000000007', '327361',  'Humira',        'BN'),
  ('e0000000-0000-0000-0000-000000000008', '7646',    'Omeprazole',    'IN')
ON CONFLICT (id) DO NOTHING;

-- ─── Claims ───────────────────────────────────────────────────────────────────
-- Mix of statuses and anomaly scenarios to exercise the full dashboard
INSERT INTO claims (
  id, patient_id, payer_id, drug_id,
  patient_name, insurance_provider, medication, amount,
  status, submitted_by,
  anomaly_flag, anomaly_reason,
  verification_status, verification_sources,
  created_at, updated_at
) VALUES

-- 1. Clean — approved
( 'f0000000-0000-0000-0000-000000000001',
  'b0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001',
  'James Holloway', 'Aetna', 'Lisinopril', 45.00,
  'approved', 'a0000000-0000-0000-0000-000000000001',
  false, null, 'verified', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '6 days', NOW() - INTERVAL '6 days' ),

-- 2. Clean — pending
( 'f0000000-0000-0000-0000-000000000002',
  'b0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000002',
  'Maria Santos', 'Cigna', 'Metformin', 30.00,
  'pending', 'a0000000-0000-0000-0000-000000000001',
  false, null, 'verified', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' ),

-- 3. Clean — approved, Medicare
( 'f0000000-0000-0000-0000-000000000003',
  'b0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000005', 'e0000000-0000-0000-0000-000000000005',
  'Linda Foster', 'Medicare', 'Amoxicillin', 25.00,
  'approved', 'a0000000-0000-0000-0000-000000000002',
  false, null, 'verified', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days' ),

-- 4. Flagged — high-value Ozempic
( 'f0000000-0000-0000-0000-000000000004',
  'b0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000004', 'e0000000-0000-0000-0000-000000000004',
  'David Park', 'Humana', 'Ozempic', 1200.00,
  'flagged', 'a0000000-0000-0000-0000-000000000001',
  true, 'Specialty medication requires formulary and prior authorization review. Claim amount exceeds the automated high-value threshold.',
  'review_required', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' ),

-- 5. Flagged — specialty Wegovy
( 'f0000000-0000-0000-0000-000000000005',
  'b0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000006',
  'Carlos Nguyen', 'Blue Cross Blue Shield', 'Wegovy', 850.00,
  'flagged', 'a0000000-0000-0000-0000-000000000001',
  true, 'Specialty medication requires formulary and prior authorization review.',
  'review_required', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' ),

-- 6. Rejected — high-value specialty Humira
( 'f0000000-0000-0000-0000-000000000006',
  'b0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000007',
  'James Holloway', 'Aetna', 'Humira', 2500.00,
  'rejected', 'a0000000-0000-0000-0000-000000000002',
  true, 'Specialty medication requires formulary and prior authorization review. Claim amount exceeds the automated high-value threshold.',
  'review_required', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day' ),

-- 7. Pending — high-value Atorvastatin
( 'f0000000-0000-0000-0000-000000000007',
  'b0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000003',
  'Maria Santos', 'Cigna', 'Atorvastatin', 1100.00,
  'pending', 'a0000000-0000-0000-0000-000000000001',
  true, 'Claim amount exceeds the automated high-value threshold.',
  'review_required', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' ),

-- 8. Clean — approved, Omeprazole
( 'f0000000-0000-0000-0000-000000000008',
  'b0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000005', 'e0000000-0000-0000-0000-000000000008',
  'Linda Foster', 'Medicare', 'Omeprazole', 35.00,
  'approved', 'a0000000-0000-0000-0000-000000000001',
  false, null, 'verified', ARRAY['payer-directory','formulary-rules','historical-claim-risk'],
  NOW(), NOW() )

ON CONFLICT (id) DO NOTHING;

-- ─── Audit log ────────────────────────────────────────────────────────────────
INSERT INTO audit_log (user_id, action, claim_id, timestamp) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'submitted claim (verified)',         'f0000000-0000-0000-0000-000000000001', NOW() - INTERVAL '6 days'),
  ('a0000000-0000-0000-0000-000000000001', 'updated claim status to approved',   'f0000000-0000-0000-0000-000000000001', NOW() - INTERVAL '6 days'),
  ('a0000000-0000-0000-0000-000000000001', 'submitted claim (verified)',         'f0000000-0000-0000-0000-000000000002', NOW() - INTERVAL '5 days'),
  ('a0000000-0000-0000-0000-000000000002', 'submitted claim (verified)',         'f0000000-0000-0000-0000-000000000003', NOW() - INTERVAL '4 days'),
  ('a0000000-0000-0000-0000-000000000002', 'updated claim status to approved',   'f0000000-0000-0000-0000-000000000003', NOW() - INTERVAL '4 days'),
  ('a0000000-0000-0000-0000-000000000001', 'submitted claim (review_required)',  'f0000000-0000-0000-0000-000000000004', NOW() - INTERVAL '3 days'),
  ('a0000000-0000-0000-0000-000000000001', 'submitted claim (review_required)',  'f0000000-0000-0000-0000-000000000005', NOW() - INTERVAL '2 days'),
  ('a0000000-0000-0000-0000-000000000002', 'submitted claim (review_required)',  'f0000000-0000-0000-0000-000000000006', NOW() - INTERVAL '2 days'),
  ('a0000000-0000-0000-0000-000000000002', 'updated claim status to rejected',   'f0000000-0000-0000-0000-000000000006', NOW() - INTERVAL '1 day'),
  ('a0000000-0000-0000-0000-000000000001', 'submitted claim (review_required)',  'f0000000-0000-0000-0000-000000000007', NOW() - INTERVAL '1 day'),
  ('a0000000-0000-0000-0000-000000000001', 'submitted claim (verified)',         'f0000000-0000-0000-0000-000000000008', NOW())
ON CONFLICT DO NOTHING;
