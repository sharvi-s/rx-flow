"""
RxFlow — FastAPI application entrypoint
Run: uvicorn app.main:app --reload --port 8001
Docs: http://localhost:8001/docs
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")

app = FastAPI(
    title="RxFlow API",
    description="Pharmacy claim management system — Care RX, Sherman TX",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "RxFlow API — v1.0.0", "docs": "/docs"}
