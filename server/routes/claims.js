const express = require('express');
const router = express.Router();
const db = require('../config/db');
const auth = require('../middleware/auth');

const serviceUrl = process.env.FASTAPI_SERVICE_URL || 'http://localhost:8001';

async function upsertPatient(name) {
  const existing = await db.query('SELECT id FROM patients WHERE full_name = $1 LIMIT 1', [name]);
  if (existing.rows.length) return existing.rows[0].id;
  const inserted = await db.query('INSERT INTO patients (full_name) VALUES ($1) RETURNING id', [name]);
  return inserted.rows[0].id;
}

async function upsertPayer(name) {
  const result = await db.query(
    `INSERT INTO payers (name, payer_type) VALUES ($1, 'commercial')
     ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id`,
    [name]
  );
  return result.rows[0].id;
}

async function upsertDrug(name, rxcui) {
  if (rxcui) {
    const result = await db.query(
      `INSERT INTO drugs (rxcui, name) VALUES ($1, $2)
       ON CONFLICT (rxcui) DO UPDATE SET name = EXCLUDED.name RETURNING id`,
      [rxcui, name]
    );
    return result.rows[0].id;
  }
  const existing = await db.query('SELECT id FROM drugs WHERE name ILIKE $1 LIMIT 1', [name]);
  if (existing.rows.length) return existing.rows[0].id;
  const inserted = await db.query('INSERT INTO drugs (name) VALUES ($1) RETURNING id', [name]);
  return inserted.rows[0].id;
}

async function verifyClaim(payload) {
  try {
    const response = await fetch(`${serviceUrl}/api/v1/insurance/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`Verification service returned ${response.status}`);
    return response.json();
  } catch (err) {
    console.error('Insurance verification failed:', err.message);
    return {
      verification_status: 'service_unavailable',
      verification_sources: ['payer-directory', 'formulary-rules', 'historical-claim-risk'],
      anomaly_flag: Number(payload.amount) > 1000,
      anomaly_reason: Number(payload.amount) > 1000 ? 'Claim amount exceeds the automated high-value threshold.' : null,
    };
  }
}

router.get('/', auth, async (req, res) => {
  try {
    const result = await db.query(
      'SELECT claims.*, users.name as submitted_by_name FROM claims LEFT JOIN users ON claims.submitted_by = users.id ORDER BY created_at DESC'
    );
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

router.post('/', auth, async (req, res) => {
  const { patient_name, insurance_provider, medication, amount, rxcui } = req.body;
  try {
    const [verification, patient_id, payer_id, drug_id] = await Promise.all([
      verifyClaim({ patient_name, insurance_provider, medication, amount: Number(amount) }),
      upsertPatient(patient_name),
      upsertPayer(insurance_provider),
      upsertDrug(medication, rxcui || null),
    ]);
    const result = await db.query(
      `INSERT INTO claims (
        patient_id, payer_id, drug_id,
        patient_name, insurance_provider, medication, amount,
        submitted_by, anomaly_flag, anomaly_reason, verification_status, verification_sources
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) RETURNING *`,
      [
        patient_id, payer_id, drug_id,
        patient_name, insurance_provider, medication, amount,
        req.user.id,
        verification.anomaly_flag,
        verification.anomaly_reason,
        verification.verification_status,
        verification.verification_sources,
      ]
    );
    await db.query(
      'INSERT INTO audit_log (user_id, action, claim_id) VALUES ($1, $2, $3)',
      [req.user.id, `submitted claim (${verification.verification_status})`, result.rows[0].id]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

router.patch('/:id/status', auth, async (req, res) => {
  const { status } = req.body;
  try {
    const result = await db.query(
      'UPDATE claims SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *',
      [status, req.params.id]
    );
    await db.query(
      'INSERT INTO audit_log (user_id, action, claim_id) VALUES ($1, $2, $3)',
      [req.user.id, `updated claim status to ${status}`, req.params.id]
    );
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

router.get('/stats', auth, async (req, res) => {
  try {
    const result = await db.query(`
      SELECT
        COUNT(*)                                      AS total,
        COUNT(*) FILTER (WHERE status = 'pending')   AS pending,
        COUNT(*) FILTER (WHERE status = 'approved')  AS approved,
        COUNT(*) FILTER (WHERE status = 'rejected')  AS rejected,
        COUNT(*) FILTER (WHERE status = 'flagged')   AS flagged_status,
        COUNT(*) FILTER (WHERE anomaly_flag = true)  AS anomaly_flagged
      FROM claims
    `);
    const row = result.rows[0];
    res.json({
      total:          parseInt(row.total),
      pending:        parseInt(row.pending),
      approved:       parseInt(row.approved),
      rejected:       parseInt(row.rejected),
      flagged:        parseInt(row.anomaly_flagged),
      flagged_status: parseInt(row.flagged_status),
    });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

module.exports = router;
