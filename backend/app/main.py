import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the root of the backend/app is in Python path so imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import Base, engine
from src.core.seed import seed_data

# Import routers
from api.auth import router as auth_router
from api.copilot import router as copilot_router
from api.transactions import router as transactions_router
from api.budgets import router as budgets_router
from api.subscriptions import router as subscriptions_router
from api.savings import router as savings_router
from api.fraud import router as fraud_router
from api.wellness import router as wellness_router
from api.reports import router as reports_router

app = FastAPI(
    title="Financial Health Advisor API",
    description="REST API backend for the Financial Wellness & Budgeting Platform.",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(copilot_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(budgets_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(savings_router, prefix="/api/v1")
app.include_router(fraud_router, prefix="/api/v1")
app.include_router(wellness_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    # Make sure all models are imported to register them on the Base metadata
    import models
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")
    
    # Auto-seed dummy data
    try:
        await seed_data()
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Error seeding database on startup: {e}")

@app.get("/")
async def root():
    return {"message": "FinPilot API Backend is running."}
