const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');

const serviceUrl = process.env.FASTAPI_SERVICE_URL || 'http://localhost:8001';

router.get('/search', auth, async (req, res) => {
  const query = String(req.query.query || '').trim();
  if (query.length < 2) return res.json({ query, results: [] });

  try {
    const response = await fetch(`${serviceUrl}/api/v1/medications/search?query=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error(`Medication service returned ${response.status}`);
    res.json(await response.json());
  } catch (err) {
    console.error('RxNorm search failed:', err.message);
    res.status(502).json({ message: 'Medication search is unavailable' });
  }
});

module.exports = router;
