import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# --------------------------------------------------
# Logging configuration
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("medical-ai-backend")

# --------------------------------------------------
# Application lifespan (startup / shutdown)
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Medical AI Backend")

    # Startup
    try:
        from database import db
        await db.command("ping")
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database startup check failed: {e}")
        # DO NOT crash the app – let health endpoint show degraded state

    yield

    # Shutdown
    logger.info("🛑 Shutting down Medical AI Backend")
    try:
        from database import client
        client.close()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.error(f"⚠️ Database shutdown issue: {e}")

# --------------------------------------------------
# FastAPI app
# --------------------------------------------------
app = FastAPI(
    title="Medical AI Backend",
    description="AI-powered medical diagnosis and health monitoring system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --------------------------------------------------
# CORS configuration
# --------------------------------------------------
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Global exception handler
# --------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# --------------------------------------------------
# REQUIRED: Root health endpoint (Render / Railway)
# --------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Medical AI Backend",
        "version": "1.0.0"
    }

# --------------------------------------------------
# Optional detailed health check
# --------------------------------------------------
@app.get("/health")
async def health_check():
    db_status = "unknown"
    try:
        from database import db
        await db.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }

# --------------------------------------------------
# Routers
# --------------------------------------------------
try:
    from routes import (
        auth,
        prediction,
        voice_assistant,
        chat,
        user_dashboard,
        admin_dashboard,
        notifications,
    )

    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(prediction.router, prefix="/predict", tags=["Predictions"])
    app.include_router(voice_assistant.router, tags=["Voice Assistant"])
    app.include_router(chat.router, tags=["Chat"])
    app.include_router(user_dashboard.router, prefix="/dashboard", tags=["User Dashboard"])
    app.include_router(admin_dashboard.router, prefix="/admin", tags=["Admin Dashboard"])
    app.include_router(notifications.router, tags=["Notifications"])

    logger.info("✅ All routers loaded successfully")

except Exception as e:
    logger.error(f"❌ Router loading failed: {e}")
    # Do NOT raise – allow health endpoint to stay alive
