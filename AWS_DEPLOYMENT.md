# AWS Deployment — RxFlow

This project can run locally with Docker Compose and also deploy the FastAPI backend to AWS ECS using an external PostgreSQL database on AWS RDS.

## What changed
- Backend now loads `.env` values automatically via `python-dotenv`.
- CORS origins are configurable via `CORS_ORIGINS`.
- Added `docker-compose.ecs.yml` for ECS deployment.
- Added `.env.example` for local and cloud environment variables.

## Deploying to AWS RDS + ECS

### 1. Create AWS RDS Postgres

1. Create an AWS RDS PostgreSQL instance (15.x or compatible).
2. Create a database named `rxflow`.
3. Create a user and password for the app.
4. Note the host, port, user, password, and database name.

Example connection string:

```bash
DATABASE_URL=postgresql+asyncpg://rxflow:<password>@<rds-host>:5432/rxflow
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and update the values.

```bash
cp .env.example .env
```

Then edit `.env`:
- `DATABASE_URL` → your AWS RDS endpoint
- `ANTHROPIC_API_KEY` → your API key
- `CORS_ORIGINS` → allowed frontend origins

### 3. Create an ECS Docker context

If you have Docker CLI configured for ECS:

```bash
docker context create ecs rxflow-ecs
docker context use rxflow-ecs
```

### 4. Deploy the API container to ECS

```bash
docker compose -f docker-compose.ecs.yml --env-file .env up
```

This will build and deploy the `api` container to ECS. The backend will connect to AWS RDS via `DATABASE_URL`.

### 5. Confirm live API

Once deployed, the ECS service should expose the FastAPI app on port `8001`.

- Health: `http://<ecs-service-endpoint>:8001/api/v1/health`
- Docs: `http://<ecs-service-endpoint>:8001/docs`

## Notes
- The ECS deployment file does not deploy the database container.
- RDS replaces the local PostgreSQL service used by `docker-compose.yml`.
- Use `docker-compose.yml` for local development and `docker-compose.ecs.yml` for cloud deployment.

## Local development

```bash
docker compose up --build
```

If you want to run locally against RDS, set `DATABASE_URL` in `.env` to point at your RDS instance and start the backend normally.
