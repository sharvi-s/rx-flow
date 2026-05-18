# 💊 RxFlow

> **Intelligent claim management system** with **AI-powered anomaly detection**, **real-time dashboard**, and **7-layer validation**.

---

## 🚀 What's This?

RxFlow automates claim processing with:

| Feature | What It Does |
|---------|-------------|
| 📋 **Smart Submission** | Submit claims with instant validation |
| 🤖 **AI Flagging** | Claude API explains anomalous claims |
| 🔎 **RxNorm Search** | Live medication lookup replaces manual free-text entry |
| 📊 **Live Dashboard** | Real-time stats and charts |
| ✅ **Workflow** | Approve/reject with one click |
| 🔍 **Search & Filter** | Find claims instantly |

---

## 🏗️ Architecture

```
┌──────────────────────────────┐
│     React Dashboard          │
│  • Charts & claim management │
│  • Real-time stats           │
└───────────────┬──────────────┘
                │ (API)
                ▼
┌──────────────────────────────┐
│    Node.js API Gateway       │
│  • Auth, claims, audit log   │
└───────────────┬──────────────┘
                │ (service calls)
                ▼
┌──────────────────────────────┐
│    FastAPI Service Layer     │
│  • Insurance verification    │
│  • RxNorm + Claude workflows │
└───────────────┬──────────────┘
                │ (pg)
                ▼
┌──────────────────────────────┐
│   PostgreSQL Database        │
│  • Data & audit trails       │
└──────────────────────────────┘
```

---

## 📚 Core Features

### 1️⃣ **Insurance Verification**

Every claim is verified across 3 service-layer sources:

- Payer directory rules
- Formulary and prior authorization rules
- Historical claim-risk thresholds

💡 Validation happens before database storage.

### 2️⃣ **AI Anomaly Detection**

Claude API flags suspicious patterns:
- High-value transactions
- Extended medication periods
- Large quantities
- Unusual refill patterns

🤖 See AI reasoning with the "Explain" button.

### 3️⃣ **RxNorm Medication Search**

Medication entry uses the RxNorm API through the FastAPI service layer, so users can pick normalized medication names and RxCUIs instead of relying on manual text entry.

### 4️⃣ **Dashboard**

- **Dashboard** — Stats cards, charts, recent claims
- **Claims** — Full list with search and filters
- **Audit Log** — Complete action history

---

## 🎯 API Endpoints

Node API base: `http://localhost:8050/api`

FastAPI service docs: `http://localhost:8001/docs`

### Claims

```bash
# Submit
POST /api/claims
{ "patient_name": "...", "insurance_provider": "Aetna", "medication": "Atorvastatin", "amount": 150.00 }

# List
GET /api/claims

# Get stats
GET /api/claims/stats

# Update
PATCH /api/claims/{id}/status
{ "status": "approved" }
```

Medication search: `GET /api/medications/search?query=atorvastatin`

Interactive FastAPI docs: **http://localhost:8001/docs**

---

## 🏃 Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/sharvi-s/rx-flow.git
cd rx-flow
docker compose up --build
```

**Ports:**
- React app: http://localhost:3000
- Node API: http://localhost:8050
- FastAPI service/docs: http://localhost:8001/docs
- PostgreSQL: localhost:5432

### Local Setup

```bash
# FastAPI service
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
uvicorn app.main:app --reload --port 8001

# Node API
cd server
npm install
export DB_USER=rxflow DB_HOST=localhost DB_NAME=rxflow DB_PASSWORD=rxflow DB_PORT=5432
export JWT_SECRET=rxflow_secret_key_2026 FASTAPI_SERVICE_URL=http://localhost:8001
npm run dev

# Frontend (separate terminal)
cd client
npm install
npm start
```

---

## 🧪 Testing

```bash
# Submit claim
curl -X POST http://localhost:8050/api/claims \
  -H "Content-Type: application/json" \
  -d '{"patient_name": "Ada Lovelace", "insurance_provider": "Aetna", "medication": "Atorvastatin", "amount": 150.00}'

# Get stats
curl http://localhost:8050/api/claims/stats | jq
```

---

## 📦 Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, Recharts |
| API Gateway | Node.js, Express |
| Service Layer | Python, FastAPI, Uvicorn |
| Database | PostgreSQL 15 |
| AI | Claude API |
| Medication API | RxNorm |
| Container | Docker, Docker Compose |

---

## 📁 Project Structure

```
rx-flow/
├── backend/          # FastAPI app
│   ├── app/main.py
│   ├── tests/test_main.py
│   ├── requirements.txt
│   └── Dockerfile
├── server/           # Node.js API gateway
│   ├── routes/
│   ├── config/db.js
│   └── Dockerfile
├── client/           # React dashboard
│   ├── src/pages/Dashboard.js
│   ├── package.json
│   └── public/
├── db/init.sql       # Normalized PostgreSQL schema
├── docker-compose.yml
└── README.md
```

---

## 🚀 Deployment

### Local
```bash
docker compose up --build
```

### Production
See [DEPLOYMENT.md](DEPLOYMENT.md) for AWS setup.

---

## 🛠️ Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📝 Environment Variables

```bash
DB_USER=rxflow
DB_HOST=localhost
DB_NAME=rxflow
DB_PASSWORD=rxflow
DB_PORT=5432
FASTAPI_SERVICE_URL=http://localhost:8001
ANTHROPIC_API_KEY=sk-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CORS_ORIGINS=http://localhost:3000
```

---

## 📄 License

MIT — See [LICENSE](LICENSE)

---

## 🔗 Links

- **Docs**: http://localhost:8001/docs
- **GitHub**: https://github.com/sharvi-s/rx-flow
- **Issues**: GitHub Issues
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
