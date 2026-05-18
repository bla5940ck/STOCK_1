"""
FastAPI application initialization and configuration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from src.config import get_settings
from src.db.database import init_db, close_db, get_db
from src.utils.logger import init_logger, get_logger
from src.exceptions import ApplicationError, SignatureError
from src.api.webhooks import verify_webhook_request, WebhookEventHandler

# Initialize logger
logger = init_logger()
app_logger = get_logger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    app_logger.info("Application starting up...")
    try:
        await init_db()
        app_logger.info("✅ Database initialized")
    except Exception as e:
        app_logger.error(f"Database initialization failed (app will continue): {e}")
    
    yield
    # Shutdown
    app_logger.info("Application shutting down...")
    try:
        await close_db()
        app_logger.info("✅ Database closed")
    except Exception as e:
        app_logger.error(f"Database shutdown error: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title="LINE Bot US Stock 美股與新聞助理",
        description="Real-time US stock market and economic news LINE Bot",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Error handler
    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=400,
            content={
                "error_code": exc.error_code,
                "error_message": exc.message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # Info endpoint
    @app.get("/info")
    async def info():
        """Application info endpoint"""
        return {
            "name": "LINE Bot US Stock 美股與新聞助理",
            "version": "0.1.0",
            "environment": "production" if not settings.DEBUG else "development",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # Webhook endpoint with signature verification
    @app.post("/webhook/line")
    async def line_webhook(
        payload: dict = Depends(verify_webhook_request),
        db: AsyncSession = Depends(get_db),
    ):
        """
        LINE Messaging API Webhook endpoint.
        
        Receives events from LINE server, verifies signature, and processes them.
        Signature verification uses HMAC-SHA256.
        """
        request_id = str(uuid.uuid4())
        app_logger.info(f"[{request_id}] Webhook received with {len(payload.get('events', []))} events")
        
        try:
            handler = WebhookEventHandler(db)
            response = await handler.handle_webhook(payload)
            app_logger.info(f"[{request_id}] Webhook processing complete")
            return response
        except Exception as e:
            app_logger.error(f"[{request_id}] Webhook processing error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )

    app_logger.info("✅ FastAPI application created successfully")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
