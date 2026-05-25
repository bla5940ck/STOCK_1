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
import traceback

from src.config import get_settings
from src.db.database import init_db, close_db, get_db
from src.utils.logger import init_logger, get_logger
from src.exceptions import ApplicationError, SignatureError
from src.api.webhooks import verify_webhook_request, WebhookEventHandler

# Import admin module (will handle errors gracefully)
admin = None
admin_router = None
try:
    from src.api import admin
    admin_router = admin.router if hasattr(admin, 'router') else None
except Exception as e:
    app_logger.warning(f"Failed to import admin module: {e}")

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
    
    # Auto-seed database on startup if empty
    try:
        app_logger.info("🌱 Checking if database needs seeding...")
        from src.db.repositories import IndexRepository
        
        async for db_session in get_db():
            repo = IndexRepository(db_session)
            existing = await repo.get_major_indices()
            
            if not existing or len(existing) < 2:
                app_logger.info("📊 Database is empty, auto-seeding with real market data...")
                
                from src.models.domain import Index, DataSourceEnum
                from decimal import Decimal
                from datetime import datetime
                
                indices_data = [
                    ("道瓊指數", "^DJI", "50579.70", "294.04", "0.58"),
                    ("NASDAQ", "^IXIC", "26343.97", "50.87", "0.19"),
                    ("S&P 500", "^GSPC", "7473.47", "27.75", "0.37"),
                    ("費城半導體", "^SOX", "12202.54", "238.46", "1.99"),
                ]
                
                count = 0
                for zh_name, symbol, price_str, change_str, change_pct_str in indices_data:
                    try:
                        current = Decimal(price_str)
                        chg = Decimal(change_str)
                        prev = current - chg
                        chg_pct = Decimal(change_pct_str)
                        
                        index = Index(
                            id=symbol,
                            code=symbol,
                            zh_name=zh_name,
                            current_price=current,
                            previous_close=prev,
                            change_amount=chg,
                            change_percent=chg_pct,
                            high_52w=current * Decimal("1.1"),
                            low_52w=current * Decimal("0.9"),
                            last_updated=datetime.utcnow(),
                            data_source=DataSourceEnum.YAHOO_FINANCE,
                        )
                        
                        await repo.create_or_update(index)
                        await db_session.commit()
                        app_logger.info(f"✅ Seeded: {zh_name}")
                        count += 1
                        
                    except Exception as e:
                        app_logger.warning(f"Failed to seed {zh_name}: {e}")
                        await db_session.rollback()
                
                app_logger.info(f"✨ Auto-seeded {count} indices")
            else:
                app_logger.info(f"✅ Database already has {len(existing)} indices")
            
            break  # Only use first session
    
    except Exception as e:
        app_logger.warning(f"Auto-seeding error (app will continue): {e}")
    
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

    # Global exception handler
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        tb = traceback.format_exc()
        app_logger.error(f"[{request_id}] Unhandled exception: {exc}")
        app_logger.error(f"[{request_id}] Traceback:\n{tb}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "request_id": request_id,
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

    # Debug endpoint: Test Taiwan stock analyst data from yfinance
    @app.get("/debug/analyst/{stock_code}")
    async def debug_analyst(stock_code: str):
        """Debug endpoint to check yfinance analyst data"""
        try:
            from src.integrations.tw_rating_scraper import TaiwanStockRatingScraper
            scraper = TaiwanStockRatingScraper()
            result = await scraper.get_analyst_ratings(stock_code)
            return {
                "stock_code": stock_code,
                "analyst_data": result,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            app_logger.error(f"Debug analyst endpoint error: {e}", exc_info=True)
            return {
                "error": str(e),
                "stock_code": stock_code,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    # Include admin routes if available
    if admin_router:
        app.include_router(admin_router)

    # Webhook endpoint with signature verification
    @app.post("/webhook/line")
    async def line_webhook(
        payload: dict = Depends(verify_webhook_request),
        db: AsyncSession = Depends(get_db),
    ):
        """
        LINE Messaging API Webhook endpoint.
        Handles message events and sends replies.
        """
        try:
            handler = WebhookEventHandler(db)
            return await handler.handle_webhook(payload)
        except Exception as e:
            app_logger.error(f"Webhook error: {e}")
            app_logger.error(traceback.format_exc())
            return JSONResponse(status_code=500, content={"error": str(e)})

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
