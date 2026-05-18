const express = require('express');
const router = express.Router();
const Anthropic = require('@anthropic-ai/sdk');
const auth = require('../middleware/auth');
const db = require('../config/db');

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

router.post('/explain/:claimId', auth, async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM claims WHERE id = $1', [req.params.claimId]);
    if (!result.rows.length) return res.status(404).json({ message: 'Claim not found' });
    
    const claim = result.rows[0];
    
    const message = await anthropic.messages.create({
      model: 'claude-opus-4-5',
      max_tokens: 256,
      messages: [{
        role: 'user',
        content: `You are a pharmacy claims analyst. Analyze this insurance claim and explain in 2-3 clear sentences why it was flagged as anomalous and what a pharmacist should check:

Patient: ${claim.patient_name}
Medication: ${claim.medication}
Insurance Provider: ${claim.insurance_provider}
Amount: $${claim.amount}
Anomaly Reason: ${claim.anomaly_reason}

Be specific, professional, and helpful. Keep it under 3 sentences.`
      }]
    });

    const explanation = message.content[0].text;
    
    await db.query('UPDATE claims SET anomaly_reason = $1 WHERE id = $2', 
      [explanation, claim.id]);

    res.json({ explanation });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: err.message });
  }
});

module.exports = router;