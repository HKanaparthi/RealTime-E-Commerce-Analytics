"""
ShopStream FastAPI Application

Main FastAPI application with CORS, routes, and lifecycle management.
Serves REST API and WebSocket endpoints for real-time analytics.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
from contextlib import asynccontextmanager

from config import settings
from routes import metrics, websocket
from models import init_database
from utils.alerts import AlertDetector
from models import get_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Background task for alert detection
alert_task = None


async def run_alert_detection():
    """
    Background task that runs alert detection every minute.
    Monitors metrics and creates alerts for anomalies.
    """
    logger.info("🔍 Starting alert detection task...")

    while True:
        try:
            session = get_session()
            detector = AlertDetector(session)

            # Run all alert checks
            detector.run_all_checks()

            session.close()

            # Wait 1 minute before next check
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Error in alert detection: {e}")
            await asyncio.sleep(60)  # Continue even on error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for FastAPI application.
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"👨‍💻 Built by {settings.DEVELOPER}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")

    # Initialize database (create tables if needed)
    try:
        init_database()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️  Database initialization warning: {e}")

    # Start background tasks
    global alert_task
    alert_task = asyncio.create_task(run_alert_detection())
    logger.info("✅ Background tasks started")

    logger.info(f"🎉 {settings.APP_NAME} is ready!")
    logger.info(f"📊 API: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"📚 Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info(f"🔌 WebSocket: ws://{settings.API_HOST}:{settings.API_PORT}/ws/metrics\n")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")

    # Cancel background tasks
    if alert_task:
        alert_task.cancel()
        try:
            await alert_task
        except asyncio.CancelledError:
            pass

    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=f"Real-time e-commerce analytics platform built by {settings.DEVELOPER}",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(metrics.router)
app.include_router(websocket.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "developer": settings.DEVELOPER,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "metrics": "/api/metrics",
            "websocket": "/ws/metrics",
        }
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Health check for monitoring and load balancers"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": str(exc)
        }
    )


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
