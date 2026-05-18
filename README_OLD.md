# RxFlow — Pharmacy Claim Management System

Full-stack pharmacy management system built for **Care RX, Sherman TX**.  
Digitizes paper-based insurance claim workflows with a FastAPI backend, PostgreSQL database, and React dashboard — with an AI anomaly detection layer powered by the Claude API.

---

## Architecture

```
rxflow/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── db/           # SQLAlchemy engine, schema.sql
│   │   ├── models/       # ORM models (Claim, Patient, Drug, Payer, Prescriber)
│   │   ├── schemas/      # Pydantic v2 request/response schemas
│   │   ├── services/     # Business logic (validation, AI flag, CRUD)
│   │   └── main.py       # App entrypoint
│   ├── tests/            # Pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Tech Stack

| Layer       | Technology                              |
|-------------|------------------------------------------|
| Backend     | Python 3.12, FastAPI, Uvicorn            |
| ORM         | SQLAlchemy 2.0 (async + mapped_column)   |
| Database    | PostgreSQL 15                            |
| Validation  | Pydantic v2                              |
| AI Layer    | Anthropic Claude API (tool use)          |
| Container   | Docker, Docker Compose                   |
| Testing     | Pytest, pytest-asyncio                   |

---

## Quick Start

### Option 1 — Docker (recommended)
```bash
git clone https://github.com/yourusername/rxflow
cd rxflow
docker-compose up --build
```
API: http://localhost:8001  
Docs: http://localhost:8001/docs

### Option 2 — Local
```bash
# 1. Start Postgres
psql -U postgres -c "CREATE DATABASE rxflow;"
psql -U rxflow rxflow < backend/app/db/schema.sql

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# 3. Set env
export DATABASE_URL=postgresql+asyncpg://rxflow:rxflow@localhost:5432/rxflow

# 4. Run
uvicorn app.main:app --reload --port 8001
```

### Option 3 — AWS RDS + ECS
1. Create an AWS RDS PostgreSQL instance and a `rxflow` database.
2. Set `DATABASE_URL` to your RDS endpoint.
3. Use `docker-compose.ecs.yml` to deploy the FastAPI backend to ECS.

Example ECS deployment flow:
```bash
cp .env.example .env
# update .env with RDS and Anthropic values
docker context create ecs rxflow-ecs
docker context use rxflow-ecs
docker compose -f docker-compose.ecs.yml --env-file .env up
```

---

## API Endpoints

### Claims
| Method | Endpoint                  | Description                          |
|--------|---------------------------|--------------------------------------|
| POST   | `/api/v1/claims`          | Submit new claim (runs validation + AI flag) |
| GET    | `/api/v1/claims`          | List claims (paginated, filterable)  |
| GET    | `/api/v1/claims/stats`    | Dashboard stats                      |
| GET    | `/api/v1/claims/{id}`     | Get single claim                     |
| PATCH  | `/api/v1/claims/{id}`     | Update status / rejection code       |
| POST   | `/api/v1/claims/ai-flag`  | Run AI anomaly check                 |

### Patients, Drugs, Payers, Prescribers
Full CRUD — see `/docs` for all endpoints.

---

## Claim Processing Pipeline

Every submitted claim goes through this pipeline automatically:

```
Submit claim
    │
    ▼
7 Validation Checks
    ├── NULL_CHECK     — required fields present
    ├── AMOUNT_RANGE   — $0 < amount < $10,000
    ├── QTY_RANGE      — 0 < qty ≤ 1,000 units
    ├── DAYS_SUPPLY    — 0 < days ≤ 365
    ├── FILL_DATE      — not in the future
    ├── COPAY_RANGE    — copay ≤ claim amount
    └── REFILL_ORDER   — refill# ≤ authorized refills
    │
    ▼
AI Anomaly Detection
    ├── High claim amount (> $500)
    ├── Extended days supply (> 90 days)
    ├── High quantity dispensed (> 360 units)
    ├── Zero copay on high-value claim
    └── Refill exceeds authorized count
    │
    ▼
PostgreSQL (with audit log)
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

17 tests covering validation logic, AI flag heuristics, and claim number generation.

---

## Database Schema

**5 tables:** `patients`, `payers`, `prescribers`, `drugs`, `claims`, `audit_log`  
Full schema with indexes, triggers, and enum types in `backend/app/db/schema.sql`.

---

## Environment Variables

| Variable       | Default                                              |
|----------------|------------------------------------------------------|
| `DATABASE_URL` | `postgresql+asyncpg://rxflow:rxflow@localhost:5432/rxflow` |
| `ANTHROPIC_API_KEY` | Required for live AI flagging |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` |

---

Built by Sharvi Sriperambudur · Texas A&M University · Care RX, Sherman TX
