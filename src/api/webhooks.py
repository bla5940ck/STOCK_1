"""
LINE Webhook signature verification and routing.
"""

import hmac
import hashlib
import base64
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.exceptions import SignatureError
from src.utils.logger import get_logger
from src.db.database import get_db
from src.db.repositories import QueryLogRepository
from src.models.database import QueryTypeEnum, QueryStatusEnum

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

        if not text:
            return None

        logger.info(f"Message from {user_id}: {text}")

        # TODO: Route to appropriate handler based on query type
        # This will be implemented in Phase 3-4 handlers

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

        # TODO: Handle Taiwan stock lookup postback
        # This will be implemented in Phase 6

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

        responses = []
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

                # Store response for delivery
                if response_text and reply_token:
                    responses.append({
                        "reply_token": reply_token,
                        "text": response_text
                    })

            except Exception as e:
                logger.error(f"Error processing event: {e}")

        # TODO: Send responses to LINE API (T043)

        return JSONResponse(status_code=200, content={"message": "OK"})
