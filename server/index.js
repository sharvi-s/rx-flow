const express = require('express');
const cors = require('cors');
require('dotenv').config();

const db = require('./config/db');
const app = express();

app.use(cors());
app.use(express.json());

// Test route
app.get('/', (req, res) => {
  res.json({ message: 'RxFlow API running' });
});

const PORT = process.env.PORT || 5000;
const authRoutes = require('./routes/auth');

const claimsRoutes = require('./routes/claims');
app.use('/api/claims', claimsRoutes);

const aiRoutes = require('./routes/ai');
app.use('/api/ai', aiRoutes);

const auditRoutes = require('./routes/audit');
app.use('/api/audit', auditRoutes);

app.use('/api/auth', authRoutes);
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});