from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
import time
from app.db.database import init_db, get_db, check_db_connection
from app.middleware import setup_cors, LoggingMiddleware
from app.middleware.logging import logger
from app.config import get_settings
from app.routes import agent, property, faq
from app.observability import initialize_phoenix, shutdown_phoenix


# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup: Initialize database
    logger.info(f"Starting up {settings.app_name} v{settings.app_version}...")
    logger.info(f"Environment: {settings.app_env}")
    init_db()
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
    
    # Initialize Phoenix tracing for observability
    logger.info("Initializing Phoenix observability...")
    initialize_phoenix()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    shutdown_phoenix()


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Register middleware (order matters - they execute in reverse order)
setup_cors(app)  # CORS middleware
app.add_middleware(LoggingMiddleware)  # Logging middleware

# Register routers
app.include_router(agent.router)
app.include_router(property.router)
app.include_router(faq.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Real Estate API",
        "status": "active",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint that verifies database connectivity.
    """
    start_time = time.time()
    
    try:
        # Simple query to check database connection
        db.execute(text("SELECT 1"))
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "database": "connected",
            "response_time_ms": round(response_time * 1000, 2)
        }
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Health check failed: {str(e)}")
        
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "response_time_ms": round(response_time * 1000, 2)
        }

