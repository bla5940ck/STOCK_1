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
    
    # Pre-warm Taiwan stock cache with all available stocks (non-blocking)
    try:
        from src.integrations.tw_stock_integration import TaiwanStockClient
        client = TaiwanStockClient()
        
        async def preload_cache():
            """Load all Taiwan stocks from TWSE in background"""
            app_logger.debug("Starting Taiwan stock cache pre-load...")
            try:
                # Fetch all Taiwan stocks dynamically
                all_stocks = await client.get_all_tw_stocks()
                app_logger.info(f"Fetched {len(all_stocks)} Taiwan stocks from TWSE")
                
                # Pre-cache the top 50 most active stocks (by code order)
                # This gives users quick access to popular stocks
                stocks_to_preload = all_stocks[:50] if len(all_stocks) > 50 else all_stocks
                
                preloaded_count = 0
                for stock in stocks_to_preload:
                    try:
                        await client.fetch_tw_stock(stock['code'], retries=1)
                        preloaded_count += 1
                    except Exception as e:
                        app_logger.debug(f"Pre-load failed for {stock['code']}: {e}")
                        
                app_logger.info(f"Taiwan stock cache pre-load complete ({preloaded_count}/{len(stocks_to_preload)} stocks)")
            except Exception as e:
                app_logger.warning(f"Taiwan stock cache pre-load failed: {e}")
            finally:
                try:
                    await client.close()
                except:
                    pass
        
        # Schedule cache pre-load (don't await - run in background)
        import asyncio
        asyncio.create_task(preload_cache())
    except Exception as e:
        app_logger.warning(f"Failed to initialize Taiwan stock cache: {e}")
    
    yield
    # Shutdown
    app_logger.info("Application shutting down...")
    await close_db()
    app_logger.info("✅ Database closed")


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
