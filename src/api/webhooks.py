"""
LINE Webhook signature verification and routing.
"""

import hmac
import hashlib
import base64
import json
import uuid
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.exceptions import SignatureError
from src.utils.logger import get_logger
from src.utils.validators import validate_query_text, is_index_keyword, detect_query_type, validate_stock_code
from src.db.database import get_db
from src.db.repositories import QueryLogRepository
from src.models.database import QueryTypeEnum, QueryStatusEnum
from src.handlers.index_handler import handle_index_query
from src.handlers.stock_handler import handle_stock_query
from src.handlers.news_handler import handle_news_query
from src.handlers.tw_stock_handler import handle_tw_stock_query

logger = get_logger(__name__)


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    """
    Verify LINE Webhook signature using HMAC-SHA256.
    
    Args:
        body: Request body (raw bytes)
        signature: X-Line-Signature header value
        channel_secret: LINE Channel Secret
        
    Returns:
        True if signature is valid
        
    Raises:
        SignatureError: If signature is invalid or missing
    """
    if not signature:
        raise SignatureError("Missing X-Line-Signature header")

    # Create HMAC-SHA256 hash
    hash_object = hmac.new(
        channel_secret.encode('utf-8'),
        body,
        hashlib.sha256
    )

    # Encode as base64
    calculated_signature = base64.b64encode(hash_object.digest()).decode('utf-8')

    # Compare signatures
    if not hmac.compare_digest(calculated_signature, signature):
        raise SignatureError(f"Invalid signature. Expected: {calculated_signature}, Got: {signature}")

    return True


async def extract_webhook_signature(request: Request) -> str:
    """Extract X-Line-Signature from request header"""
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")
    return signature


async def verify_webhook_request(
    request: Request,
    signature: str = Depends(extract_webhook_signature)
) -> Dict[str, Any]:
    """
    Verify LINE Webhook request and extract body.
    
    Args:
        request: FastAPI request
        signature: X-Line-Signature header
        
    Returns:
        Parsed JSON body
        
    Raises:
        HTTPException: If signature is invalid
    """
    settings = get_settings()
    body = await request.body()

    try:
        verify_line_signature(
            body,
            signature,
            settings.LINE_CHANNEL_SECRET
        )
    except SignatureError as e:
        logger.warning(f"Webhook signature verification failed: {e.message}")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = json.loads(body)
        return payload
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")


class WebhookEventHandler:
    """Handle LINE Webhook events"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.log_repo = QueryLogRepository(db)

    async def process_message_event(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Process message event.
        
        Args:
            event: LINE message event
            
        Returns:
            Response message or None
        """
        user_id = event.get("source", {}).get("userId")
        message = event.get("message", {})
        message_type = message.get("type")
        text = message.get("text", "").strip()

        if not text or message_type != "text":
            return None

        logger.info(f"Message from {user_id}: {text}")

        try:
            # Validate and detect query type
            query_text = validate_query_text(text)
        except Exception as e:
            logger.warning(f"Query validation failed: {e}")
            await self.log_query(
                user_id=user_id,
                query_text=text,
                query_type="unknown",
                status="failed",
                error_message=str(e)
            )
            return None

        # Route based on query type
        if is_index_keyword(query_text):
            # Index query (美股, 指數)
            result = await handle_index_query(self.db)
            
            await self.log_query(
                user_id=user_id,
                query_text=query_text,
                query_type="index",
                status="success" if result.get("success") else "failed",
                error_message=result.get("error_message"),
            )
            
            return result.get("message")
        
        elif detect_query_type(query_text) == "news":
            # News query (新聞, news)
            result = await handle_news_query(self.db)
            
            await self.log_query(
                user_id=user_id,
                query_text=query_text,
                query_type="news",
                status="success" if result.get("success") else "failed",
                error_message=result.get("error_message"),
            )
            
            return result.get("message")
        
        elif detect_query_type(query_text) == "stock":
            # Stock query (AAPL, TSLA, etc.)
            try:
                stock_code = validate_stock_code(query_text)
                result = await handle_stock_query(self.db, stock_code)
                
                await self.log_query(
                    user_id=user_id,
                    query_text=query_text,
                    query_type="stock",
                    status="success" if result.get("success") else "failed",
                    error_message=result.get("error_message"),
                )
                
                return result.get("message")
            except Exception as e:
                logger.warning(f"Stock query validation failed: {e}")
                await self.log_query(
                    user_id=user_id,
                    query_text=query_text,
                    query_type="stock",
                    status="failed",
                    error_message=str(e)
                )
                return None

        logger.debug(f"Unknown query type for: {query_text}")
        return None

    async def process_postback_event(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Process postback event (button clicks).
        
        Args:
            event: LINE postback event
            
        Returns:
            Response message or None
        """
        user_id = event.get("source", {}).get("userId")
        postback_data = event.get("postback", {}).get("data", "")

        logger.info(f"Postback from {user_id}: {postback_data}")

        if not postback_data:
            logger.debug("Empty postback data")
            return None

        # Parse postback data format: "action=query&code=AAPL"
        try:
            params = {}
            for param in postback_data.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    params[key] = value

            action = params.get("action", "")
            us_code = params.get("code", "")

            # Handle Taiwan stock query action
            if action == "tw_stock_query" and us_code:
                logger.info(f"Taiwan stock query postback for {us_code}")
                
                result = await handle_tw_stock_query(self.db, us_code)
                
                await self.log_query(
                    user_id=user_id,
                    query_text=us_code,
                    query_type="tw_stock",
                    status="success" if result.get("success") else "failed",
                    error_message=result.get("error_message"),
                )
                
                return result.get("message")

            elif action == "skip":
                # User clicked "skip" button - don't respond
                logger.info(f"User {user_id} skipped Taiwan stock query")
                return None

            else:
                logger.warning(f"Unknown postback action: {action}")
                return None

        except Exception as e:
            logger.error(f"Error processing postback: {e}")
            return None

    async def log_query(
        self,
        user_id: str,
        query_text: str,
        query_type: str,
        status: str = "pending",
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a query for analytics"""
        try:
            await self.log_repo.create(
                user_id=user_id,
                query_text=query_text,
                query_type=QueryTypeEnum(query_type),
                status=QueryStatusEnum(status),
                response_time_ms=response_time_ms,
                error_message=error_message,
            )
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            await self.db.rollback()

    async def send_reply_message(
        self, reply_token: str, text: str
    ) -> bool:
        """
        Send reply message to LINE API.
        
        Args:
            reply_token: Reply token from LINE
            text: Message text to send
            
        Returns:
            True if successful
        """
        settings = get_settings()
        url = "https://api.line.biz/v2/bot/message/reply"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        }
        
        data = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": text,
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully sent reply message")
                        return True
                    else:
                        logger.error(
                            f"Failed to send reply message: {response.status}"
                        )
                        return False
        except Exception as e:
            logger.error(f"Error sending reply message: {e}")
            return False

    async def handle_webhook(self, payload: Dict[str, Any]) -> JSONResponse:
        """
        Handle LINE Webhook payload.
        
        Args:
            payload: Webhook payload from LINE
            
        Returns:
            JSON response for LINE server
        """
        destination = payload.get("destination")
        events = payload.get("events", [])

        logger.info(f"Webhook received with {len(events)} events")

        for event in events:
            event_type = event.get("type")
            reply_token = event.get("replyToken")

            try:
                response_text = None

                if event_type == "message":
                    response_text = await self.process_message_event(event)
                elif event_type == "postback":
                    response_text = await self.process_postback_event(event)
                elif event_type == "follow":
                    logger.info(f"User {event.get('source', {}).get('userId')} followed bot")
                elif event_type == "unfollow":
                    logger.info(f"User {event.get('source', {}).get('userId')} unfollowed bot")

                # Send reply to LINE if we have a message
                if response_text and reply_token:
                    await self.send_reply_message(reply_token, response_text)

            except Exception as e:
                logger.error(f"Error processing event: {e}")

        return JSONResponse(status_code=200, content={"message": "OK"})
