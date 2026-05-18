# Deployment Guide

Quick reference for deploying RxFlow to different environments.

## Local Development

### Docker Compose (Easiest)

```bash
docker compose up --build
```

**Ports:**
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Client: http://localhost:3000 (if running separately)

**Data:**
- PostgreSQL data persists in `pgdata/` volume
- Logs appear in terminal

### Manual Setup

```bash
# Terminal 1: PostgreSQL
docker run -d \
  -e POSTGRES_PASSWORD=rxflow \
  -p 5432:5432 \
  postgres:15-alpine

createdb -U postgres -h localhost rxflow
psql -U postgres -h localhost -d rxflow < backend/app/db/schema.sql

# Terminal 2: Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://postgres:rxflow@localhost:5432/rxflow
export ANTHROPIC_API_KEY=sk-...
uvicorn app.main:app --reload --port 8001

# Terminal 3: Frontend
cd client
npm install
npm start
```

---

## AWS Deployment

### Prerequisites

- AWS account with IAM permissions (EC2, RDS, ECS)
- AWS CLI configured
- Docker CLI with ECS support

### Step 1: Create RDS PostgreSQL

```bash
# Via AWS Console or CLI
aws rds create-db-instance \
  --db-instance-identifier rxflow-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username rxflow \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20
```

After creation, note the endpoint (e.g., `rxflow-db.c123456.us-east-1.rds.amazonaws.com`).

### Step 2: Create RDS Database

```bash
# Connect to RDS
psql -h rxflow-db.c123456.us-east-1.rds.amazonaws.com \
  -U rxflow -d postgres

# Create database
CREATE DATABASE rxflow;
\c rxflow
\i backend/app/db/schema.sql
```

### Step 3: Deploy Backend to ECS

```bash
# Create .env with RDS connection
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://rxflow:PASSWORD@rxflow-db.c123456.us-east-1.rds.amazonaws.com:5432/rxflow
ANTHROPIC_API_KEY=sk-YOUR-KEY
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
EOF

# Create ECS context
docker context create ecs rxflow-ecs
docker context use rxflow-ecs

# Deploy
docker compose -f docker-compose.ecs.yml --env-file .env up
```

### Step 4: Deploy Frontend

Use AWS Amplify, CloudFront + S3, or similar:

```bash
# Build React app
cd client
npm run build

# Upload to S3 (example)
aws s3 sync build/ s3://your-bucket-name --delete
```

---

## Environment Variables

### Development

```bash
DATABASE_URL=postgresql+asyncpg://rxflow:rxflow@localhost:5432/rxflow
ANTHROPIC_API_KEY=sk-...
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (AWS RDS + ECS)

```bash
DATABASE_URL=postgresql+asyncpg://rxflow:PASSWORD@rxflow-db.REGION.rds.amazonaws.com:5432/rxflow
ANTHROPIC_API_KEY=sk-...
CORS_ORIGINS=https://yourdomain.com
```

---

## Troubleshooting

### Database Connection Fails

```bash
# Test connection
psql postgresql://user:pass@host:5432/database

# Check RDS security group
# Ensure inbound rule allows PostgreSQL (5432) from your IP
```

### API Returns 502 Bad Gateway

Check ECS logs:
```bash
aws logs tail /ecs/rxflow --follow
```

### High Memory Usage

Adjust Dockerfile resources or use larger EC2 instance type.

---

## Monitoring

### CloudWatch Logs

```bash
# Stream logs
aws logs tail /ecs/rxflow --follow

# Check specific time range
aws logs filter-log-events \
  --log-group-name /ecs/rxflow \
  --start-time $(date -d '1 hour ago' +%s)000
```

### Database Metrics

AWS RDS CloudWatch dashboard shows:
- CPU utilization
- Database connections
- Storage used
- Query latency

---

## Scaling

### Horizontal (More Containers)

In ECS:
1. Go to Service
2. Update desired count
3. More instances = more concurrent requests

### Vertical (Bigger Instance)

For RDS:
1. Modify DB Instance
2. Select larger instance class
3. Apply during maintenance window

---

See [README.md](README.md) for more info.
