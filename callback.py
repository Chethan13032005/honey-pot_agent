import requests
import time
import logging
from typing import Dict

from config import get_settings

logger = logging.getLogger(__name__)


def send_final_callback(session_id: str, session: dict, max_retries: int = None, timeout: int = None):
    """
    Send final callback with retry mechanism.
    
    Args:
        session_id: Session identifier
        session: Session data dictionary
        max_retries: Maximum number of retry attempts (uses config default if None)
        timeout: Request timeout in seconds (uses config default if None)
    """
    settings = get_settings()
    
    # Use config defaults if not provided
    if max_retries is None:
        max_retries = settings.callback_retry_attempts
    if timeout is None:
        timeout = settings.callback_timeout
    
    callback_url = settings.callback_url
    
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": session["turns"],
        "extractedIntelligence": session["extracted"],
        "agentNotes": "Scammer used urgency, repetition, and threat escalation",
        "finalConfidence": session.get("confidence", 0.0)
    }
    
    logger.info(
        f"Preparing to send callback",
        extra={
            "session_id": session_id,
            "turns": session["turns"],
            "confidence": session.get("confidence", 0.0),
            "callback_url": callback_url,
        }
    )
    
    for attempt in range(max_retries):
        try:
            logger.debug(
                f"Sending callback (attempt {attempt + 1}/{max_retries})",
                extra={"session_id": session_id, "attempt": attempt + 1}
            )
            
            response = requests.post(
                callback_url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            logger.info(
                f"✅ Callback sent successfully",
                extra={
                    "session_id": session_id,
                    "status_code": response.status_code,
                    "attempt": attempt + 1,
                }
            )
            return True
            
        except requests.exceptions.Timeout:
            logger.warning(
                f"Callback timeout (attempt {attempt + 1}/{max_retries})",
                extra={"session_id": session_id}
            )
            
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Callback request failed (attempt {attempt + 1}/{max_retries})",
                extra={
                    "session_id": session_id,
                    "error": str(e),
                    "attempt": attempt + 1,
                }
            )
            
        except Exception as e:
            logger.error(
                f"Unexpected error sending callback",
                extra={
                    "session_id": session_id,
                    "error": str(e),
                    "attempt": attempt + 1,
                },
                exc_info=True
            )
        
        # Exponential backoff before retry (except on last attempt)
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.debug(f"Waiting {wait_time}s before retry")
            time.sleep(wait_time)
    
    logger.error(
        f"❌ Failed to send callback after {max_retries} attempts",
        extra={"session_id": session_id}
    )
    return False
