"""
Production-Ready Honey-Pot Scam Detection API
AI-powered agentic system that detects scam messages and autonomously engages scammers.
"""
import os
import logging
import time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from logging.handlers import RotatingFileHandler

from config import get_settings, Settings
from models import (
    IncomingRequest, MessageResponse, ErrorResponse,
    HealthResponse, DetailedHealthResponse, MetricsResponse,
    SessionResponse, SessionData, ExtractedIntelligence,
    IntelligenceResponse
)
from middleware import (
    RequestIDMiddleware, RequestLoggingMiddleware,
    SecurityHeadersMiddleware, RateLimitMiddleware
)
from detection import detect_scam, update_confidence
from agent import generate_reply, generate_exit_message
from callback import send_final_callback
from extraction import extract_all_intelligence, merge_intelligence


# -------------------------
# Logging Setup
# -------------------------

def setup_logging(settings: Settings):
    """Configure application logging with file rotation."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(settings.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count
    )
    file_handler.setLevel(settings.log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={settings.log_level}, file={settings.log_file}")


# -------------------------
# Application Lifecycle
# -------------------------

# Track application start time for uptime metrics
app_start_time = time.time()

# In-memory session store
SESSIONS: Dict[str, SessionData] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    settings = get_settings()
    setup_logging(settings)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    logger.info(f"Total sessions processed: {len(SESSIONS)}")


# -------------------------
# FastAPI Application
# -------------------------

app = FastAPI(
    title=get_settings().api_title,
    version=get_settings().api_version,
    description=get_settings().api_description,
    lifespan=lifespan,
    docs_url="/docs" if get_settings().debug else None,
    redoc_url="/redoc" if get_settings().debug else None,
)

logger = logging.getLogger(__name__)


# -------------------------
# Middleware Configuration
# -------------------------

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware (order matters - first added is outermost)
app.add_middleware(SecurityHeadersMiddleware)
if get_settings().rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=get_settings().rate_limit_requests)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# -------------------------
# Exception Handlers
# -------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"Validation error",
        extra={
            "request_id": request_id,
            "errors": exc.errors(),
        }
    )
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="validation_error",
            message="Invalid request data",
            detail=str(exc.errors()),
            request_id=request_id
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"http_{exc.status_code}",
            message=exc.detail,
            request_id=request_id
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unexpected error",
        extra={
            "request_id": request_id,
            "error": str(exc),
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            detail=str(exc) if get_settings().debug else None,
            request_id=request_id
        ).dict()
    )


# -------------------------
# Dependency Injection
# -------------------------

def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """Verify API key from request header."""
    settings = get_settings()
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# -------------------------
# Health Check Endpoints
# -------------------------

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Basic health check endpoint.
    Returns simple status to verify the API is running.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with system information.
    Includes component status and basic metrics.
    """
    settings = get_settings()
    
    # Check components
    components = {
        "api": "healthy",
        "sessions": "healthy",
        "logging": "healthy",
    }
    
    # Basic metrics
    metrics = {
        "total_sessions": len(SESSIONS),
        "active_sessions": sum(1 for s in SESSIONS.values() if not s.completed),
        "uptime_seconds": int(time.time() - app_start_time),
    }
    
    return DetailedHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        environment=settings.environment,
        components=components,
        metrics=metrics
    )


# -------------------------
# Metrics Endpoint
# -------------------------

@app.get("/metrics", response_model=MetricsResponse, tags=["Monitoring"])
async def get_metrics():
    """
    Get application metrics.
    Returns statistics about sessions, messages, and scam detection.
    """
    total_sessions = len(SESSIONS)
    active_sessions = sum(1 for s in SESSIONS.values() if not s.completed)
    completed_sessions = sum(1 for s in SESSIONS.values() if s.completed)
    total_messages = sum(s.turns for s in SESSIONS.values())
    scams_detected = sum(1 for s in SESSIONS.values() if s.confidence < 0.5)
    
    # Calculate average confidence
    if SESSIONS:
        avg_confidence = sum(s.confidence for s in SESSIONS.values()) / len(SESSIONS)
    else:
        avg_confidence = 0.0
    
    return MetricsResponse(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        total_messages=total_messages,
        scams_detected=scams_detected,
        average_confidence=round(avg_confidence, 2),
        uptime_seconds=time.time() - app_start_time
    )


# -------------------------
# Intelligence Aggregation Endpoint
# -------------------------

@app.get("/intelligence", response_model=IntelligenceResponse, tags=["Intelligence"])
async def get_intelligence(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Get aggregated intelligence from all sessions.
    
    Returns all extracted scammer data including:
    - UPI IDs
    - Phone numbers
    - Phishing links
    - Suspicious keywords
    
    Requires API key authentication.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.info(
        f"Intelligence aggregation requested",
        extra={"request_id": request_id}
    )
    
    # Aggregate all intelligence from all sessions
    all_upi_ids = []
    all_phone_numbers = []
    all_phishing_links = []
    all_keywords = []
    sessions_with_data = []
    scam_count = 0
    
    for session_id, session_data in SESSIONS.items():
        extracted = session_data.extracted
        
        # Check if session has any extracted intelligence
        has_intelligence = (
            extracted.upiIds or 
            extracted.phoneNumbers or 
            extracted.phishingLinks or 
            extracted.suspiciousKeywords
        )
        
        if has_intelligence:
            sessions_with_data.append({
                "session_id": session_id,
                "confidence": session_data.confidence,
                "turns": session_data.turns,
                "completed": session_data.completed,
                "extracted": extracted.dict(),
                "created_at": session_data.created_at.isoformat() if session_data.created_at else None,
            })
            
            # Aggregate all data
            all_upi_ids.extend(extracted.upiIds)
            all_phone_numbers.extend(extracted.phoneNumbers)
            all_phishing_links.extend(extracted.phishingLinks)
            all_keywords.extend(extracted.suspiciousKeywords)
        
        # Count scam sessions (confidence < 1.0)
        if session_data.confidence < 1.0:
            scam_count += 1
    
    # Create aggregated intelligence with unique values
    aggregated = ExtractedIntelligence(
        upiIds=list(set(all_upi_ids)),  # Remove duplicates
        phoneNumbers=list(set(all_phone_numbers)),
        phishingLinks=list(set(all_phishing_links)),
        suspiciousKeywords=list(set(all_keywords))
    )
    
    # Count unique items
    unique_counts = {
        "unique_upi_ids": len(aggregated.upiIds),
        "unique_phone_numbers": len(aggregated.phoneNumbers),
        "unique_phishing_links": len(aggregated.phishingLinks),
        "unique_keywords": len(aggregated.suspiciousKeywords),
        "total_unique_items": (
            len(aggregated.upiIds) + 
            len(aggregated.phoneNumbers) + 
            len(aggregated.phishingLinks) + 
            len(aggregated.suspiciousKeywords)
        )
    }
    
    logger.info(
        f"Intelligence aggregation completed",
        extra={
            "request_id": request_id,
            "total_sessions": len(SESSIONS),
            "sessions_with_intelligence": len(sessions_with_data),
            "unique_items": unique_counts["total_unique_items"]
        }
    )
    
    return IntelligenceResponse(
        total_sessions=len(SESSIONS),
        scam_sessions=scam_count,
        aggregated_intelligence=aggregated,
        unique_counts=unique_counts,
        sessions_with_intelligence=sessions_with_data
    )


# -------------------------
# Main Honeypot Endpoint
# -------------------------

@app.post("/honeypot/message", response_model=MessageResponse, tags=["Honeypot"])
async def handle_message(
    payload: IncomingRequest,
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Process incoming scam message and generate intelligent response.
    
    This endpoint:
    1. Detects scam indicators in the message
    2. Extracts intelligence (UPI IDs, phone numbers, URLs)
    3. Updates confidence score
    4. Generates appropriate response
    5. Sends callback when scam is confirmed
    
    Requires valid API key in x-api-key header.
    """
    settings = get_settings()
    request_id = getattr(request.state, "request_id", "unknown")
    session_id = payload.sessionId
    message_text = payload.message.text
    
    logger.info(
        f"Processing message",
        extra={
            "request_id": request_id,
            "session_id": session_id,
            "message_length": len(message_text),
        }
    )
    
    # -------------------------
    # Create or load session
    # -------------------------
    if session_id not in SESSIONS:
        logger.info(f"Creating new session", extra={"session_id": session_id})
        SESSIONS[session_id] = SessionData(
            confidence=1.0,
            turns=0,
            completed=False,
            extracted=ExtractedIntelligence(),
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
    
    session = SESSIONS[session_id]
    session.update_activity()
    
    # Add message to history for pattern detection (keep last 10)
    session.message_history.append(message_text)
    if len(session.message_history) > 10:
        session.message_history = session.message_history[-10:]
    
    # -------------------------
    # Enhanced Scam Detection
    # -------------------------
    detection = detect_scam(
        message_text,
        message_history=session.message_history[:-1],  # Exclude current message
        behavior_patterns=session.behavior_patterns
    )
    
    # -------------------------
    # PASS-THROUGH MODE: If NOT scam, let user handle it
    # -------------------------
    if not detection["is_scam"]:
        logger.info(
            f"No scam detected - passing through to user",
            extra={
                "session_id": session_id,
                "message_preview": message_text[:50] + "..." if len(message_text) > 50 else message_text,
            }
        )
        
        return MessageResponse(
            status="success",
            reply=None,  # No agent reply - user handles this
            confidence=1.0,
            session_id=session_id,
            turns=session.turns,
            agent_engaged=False,
            scam_detected=False
        )
    
    # -------------------------
    # SCAM DETECTED: Agent takes control
    # -------------------------
    logger.warning(
        f"Scam indicators detected - agent engaging",
        extra={
            "session_id": session_id,
            "flags": detection["flags"],
            "detection_confidence": detection["confidence"],
            "repetition": detection.get("repetition", {}),
            "escalation": detection.get("escalation", {}),
        }
    )
    
    # Update behavior patterns
    if "urgency" in detection["flags"]:
        session.behavior_patterns["urgency"] = session.behavior_patterns.get("urgency", 0) + 1
    if "threat" in detection["flags"]:
        session.behavior_patterns["threat"] = session.behavior_patterns.get("threat", 0) + 1
    
    # Update session confidence with enhanced decay
    session.confidence = update_confidence(
        session.confidence,
        detection["flags"],
        repetition_data=detection.get("repetition"),
        escalation_data=detection.get("escalation")
    )
    
    # Extract intelligence
    new_intelligence = extract_all_intelligence(message_text, detection["flags"])
    session.extracted = ExtractedIntelligence(
        **merge_intelligence(session.extracted.dict(), new_intelligence)
    )
    
    session.turns += 1
    
    # -------------------------
    # Intelligent Exit Strategy
    # -------------------------
    def should_exit() -> tuple[bool, str]:
        """Determine if agent should exit conversation."""
        # Exit condition 1: Confidence threshold reached
        if session.confidence <= settings.exit_confidence_threshold:
            return True, "confidence_threshold"
        
        # Exit condition 2: Sufficient intelligence collected
        has_critical_intel = (
            len(session.extracted.upiIds) > 0 or
            len(session.extracted.phoneNumbers) > 0 or
            len(session.extracted.phishingLinks) > 0
        )
        if has_critical_intel and session.turns >= 3:
            return True, "intelligence_collected"
        
        # Exit condition 3: Too many turns (safety limit)
        if session.turns >= 15:
            return True, "max_turns_reached"
        
        return False, None
    
    exit_needed, exit_reason = should_exit()
    
    if exit_needed and not session.completed:
        logger.info(
            f"Exit condition met, ending conversation",
            extra={
                "session_id": session_id,
                "exit_reason": exit_reason,
                "final_confidence": session.confidence,
                "turns": session.turns,
                "intelligence_items": (
                    len(session.extracted.upiIds) +
                    len(session.extracted.phoneNumbers) +
                    len(session.extracted.phishingLinks)
                ),
            }
        )
        
        # Send final callback (uses settings defaults)
        send_final_callback(session_id, session.dict())
        
        session.completed = True
        
        # Generate persona-appropriate exit message
        reply = generate_exit_message(
            current_persona=session.current_persona,
            extracted_intelligence=session.extracted.dict()
        )
    else:
        # Generate intelligent reply with persona switching
        try:
            reply, new_persona = generate_reply(
                confidence=session.confidence,
                last_message=message_text,
                current_persona=session.current_persona,
                extracted_intelligence=session.extracted.dict()
            )
            
            # Track persona changes
            if new_persona != session.current_persona:
                session.persona_history.append({
                    "from": session.current_persona,
                    "to": new_persona,
                    "turn": session.turns,
                    "confidence": session.confidence
                })
                session.current_persona = new_persona
                
        except Exception as e:
            logger.error(
                f"Error generating reply",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            reply = "I'm not sure I understand. Can you explain more?"
    
    logger.info(
        f"Message processed successfully - agent engaged",
        extra={
            "session_id": session_id,
            "confidence": session.confidence,
            "turns": session.turns,
            "completed": session.completed,
            "current_persona": session.current_persona,
        }
    )
    
    return MessageResponse(
        status="success",
        reply=reply,
        confidence=session.confidence,
        session_id=session_id,
        turns=session.turns,
        agent_engaged=True,
        scam_detected=True
    )


# -------------------------
# Admin Endpoints (Optional)
# -------------------------

@app.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Admin"])
async def get_session(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get session details by ID.
    Requires valid API key.
    """
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        session_id=session_id,
        data=SESSIONS[session_id]
    )


@app.get("/sessions", tags=["Admin"])
async def list_sessions(
    api_key: str = Depends(verify_api_key),
    limit: int = 100
):
    """
    List all sessions.
    Requires valid API key.
    """
    # Convert to list format
    sessions_list = [
        {"session_id": sid, "data": data.dict()}
        for sid, data in list(SESSIONS.items())[:limit]
    ]
    
    return {
        "total": len(SESSIONS),
        "returned": len(sessions_list),
        "sessions": sessions_list
    }


# -------------------------
# Root Endpoint
# -------------------------

@app.get("/", tags=["Info"])
async def root():
    """
    API information endpoint.
    """
    settings = get_settings()
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "environment": settings.environment,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
