const express = require('express');
const router = express.Router();
const db = require('../config/db');
const auth = require('../middleware/auth');

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
  const { patient_name, insurance_provider, medication, amount } = req.body;
  try {
    const anomaly = amount > 1000;
    const anomaly_reason = anomaly ? 'Amount exceeds $1000 threshold' : null;
    const result = await db.query(
      'INSERT INTO claims (patient_name, insurance_provider, medication, amount, submitted_by, anomaly_flag, anomaly_reason) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *',
      [patient_name, insurance_provider, medication, amount, req.user.id, anomaly, anomaly_reason]
    );
    await db.query(
      'INSERT INTO audit_log (user_id, action, claim_id) VALUES ($1, $2, $3)',
      [req.user.id, 'submitted claim', result.rows[0].id]
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
    const total = await db.query('SELECT COUNT(*) FROM claims');
    const pending = await db.query("SELECT COUNT(*) FROM claims WHERE status = 'pending'");
    const flagged = await db.query('SELECT COUNT(*) FROM claims WHERE anomaly_flag = true');
    const approved = await db.query("SELECT COUNT(*) FROM claims WHERE status = 'approved'");
    res.json({
      total: parseInt(total.rows[0].count),
      pending: parseInt(pending.rows[0].count),
      flagged: parseInt(flagged.rows[0].count),
      approved: parseInt(approved.rows[0].count)
    });
  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});

module.exports = router;