from fastapi import FastAPI, Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import engine, create_tables
from app.routers import (
    auth, opportunities, applications, contacts, 
    documents, tasks, rules, analytics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    await create_tables()
    logger.info("Application startup complete")
    yield
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title="Student CRM API",
    description="A comprehensive CRM system for students to track internships, jobs, and research opportunities",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(opportunities.router, prefix="/opportunities", tags=["Opportunities"])
app.include_router(applications.router, prefix="/applications", tags=["Applications"])
app.include_router(contacts.router, prefix="/contacts", tags=["Contacts"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(rules.router, prefix="/rules", tags=["Rules"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

@app.get("/")
async def root():
    return {"message": "Student CRM API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}