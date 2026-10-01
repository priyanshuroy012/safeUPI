"""
SafeUPI FastAPI application entry point.

Run:
    uvicorn main:app --reload

The prototype uses synthetic/demo transaction data and never executes
real UPI transactions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.payment import router as payment_router
from backend.api.admin import router as admin_router
from backend.api.accounts import router as accounts_router

from backend.risk_engine.risk import risk_engine_health
from backend.risk_engine.mule_detection import mule_engine_health

app = FastAPI(
    title="SafeUPI API",
    description=(
        "Adaptive fraud-prevention and transaction-network intelligence "
        "prototype for digital payments."
    ),
    version="0.1.0",
)

# Development CORS. Restrict allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payment_router)
app.include_router(admin_router)
app.include_router(accounts_router)


@app.get("/")
def root():
    return {
        "project": "SafeUPI",
        "status": "running",
        "message": "Fraud prevention + transaction network intelligence API",
    }


@app.get("/health")
def health():
    return {
        "api": "ok",
        "risk_engine": risk_engine_health(),
        "mule_detection": mule_engine_health(),
    }
