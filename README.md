# 💊 RxFlow

> **Intelligent claim management system** with **AI-powered anomaly detection**, **real-time dashboard**, and **7-layer validation**.

---

## 🚀 What's This?

RxFlow automates claim processing with:

| Feature | What It Does |
|---------|-------------|
| 📋 **Smart Submission** | Submit claims with instant validation |
| 🤖 **AI Flagging** | Claude API detects anomalies |
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
│    FastAPI Backend           │
│  • Validation & workflows    │
│  • AI anomaly detection      │
└───────────────┬──────────────┘
                │ (SQLAlchemy)
                ▼
┌──────────────────────────────┐
│   PostgreSQL Database        │
│  • Data & audit trails       │
└──────────────────────────────┘
```

---

## 📚 Core Features

### 1️⃣ **7-Layer Validation**

Every claim is validated instantly:

- Required fields present
- Amount within limits
- Quantity within bounds
- Supply period valid
- Date checks
- Copay logic valid
- Refill count valid

💡 Validation happens before database storage.

### 2️⃣ **AI Anomaly Detection**

Claude API flags suspicious patterns:
- High-value transactions
- Extended medication periods
- Large quantities
- Unusual refill patterns

🤖 See AI reasoning with the "Explain" button.

### 3️⃣ **Dashboard**

- **Dashboard** — Stats cards, charts, recent claims
- **Claims** — Full list with search and filters
- **Audit Log** — Complete action history

---

## 🎯 API Endpoints

Base: `http://localhost:8001/api/v1`

### Claims

```bash
# Submit
POST /claims
{ "patient_id": "...", "amount": 150.00, ... }

# List
GET /claims?page=1&size=20&status=pending

# Get stats
GET /claims/stats

# Update
PATCH /claims/{id}
{ "status": "approved" }
```

Full CRUD for `patients`, `drugs`, `payers`, `prescribers`.  
Interactive docs: **http://localhost:8001/docs**

---

## 🏃 Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/sharvi-s/rx-flow.git
cd rx-flow
docker compose up --build
```

**Ports:**
- Backend: http://localhost:8001
- Docs: http://localhost:8001/docs

### Local Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://rxflow:rxflow@localhost:5432/rxflow
uvicorn app.main:app --reload --port 8001

# Frontend (separate terminal)
cd client
npm install
npm start
```

---

## 🧪 Testing

```bash
# Submit claim
curl -X POST http://localhost:8001/api/v1/claims \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "123e4567...", "amount": 150.00}'

# Get stats
curl http://localhost:8001/api/v1/claims/stats | jq
```

---

## 📦 Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React, Recharts |
| Backend | FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 15 |
| AI | Claude API |
| Container | Docker, Docker Compose |

---

## 📁 Project Structure

```
rx-flow/
├── backend/          # FastAPI app
│   ├── app/main.py
│   ├── app/api/routes.py
│   ├── app/models/models.py
│   ├── app/db/session.py
│   ├── requirements.txt
│   └── Dockerfile
├── client/           # React dashboard
│   ├── src/pages/Dashboard.js
│   ├── package.json
│   └── public/
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
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
ANTHROPIC_API_KEY=sk-...
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
