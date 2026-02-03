"""
Enhanced Pydantic models for request/response validation.
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


# -------------------------
# Request Models
# -------------------------

class Message(BaseModel):
    """Message model for incoming messages."""
    sender: str = Field(..., description="Message sender identifier")
    text: str = Field(..., min_length=1, description="Message text content")
    timestamp: str = Field(..., description="Message timestamp in ISO format")
    
    @validator("text")
    def validate_text_not_empty(cls, v):
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Message text cannot be empty or whitespace only")
        return v.strip()


class IncomingRequest(BaseModel):
    """Request model for incoming honeypot messages."""
    sessionId: str = Field(..., min_length=1, description="Unique session identifier")
    message: Message = Field(..., description="Message object")
    
    @validator("sessionId")
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if not v.strip():
            raise ValueError("Session ID cannot be empty")
        return v.strip()


# -------------------------
# Response Models
# -------------------------

class MessageResponse(BaseModel):
    """Response model for message handling."""
    status: str = Field(default="success", description="Response status")
    reply: Optional[str] = Field(None, description="Agent's reply message (None if pass-through)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Current scam confidence score")
    session_id: Optional[str] = Field(None, description="Session identifier")
    turns: Optional[int] = Field(None, description="Number of conversation turns")
    agent_engaged: bool = Field(..., description="Whether agent is handling the conversation")
    scam_detected: bool = Field(..., description="Whether scam was detected in this message")


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str = Field(default="error", description="Response status")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


# -------------------------
# Session Models
# -------------------------

class ExtractedIntelligence(BaseModel):
    """Model for extracted intelligence data."""
    upiIds: List[str] = Field(default_factory=list, description="Extracted UPI IDs")
    phoneNumbers: List[str] = Field(default_factory=list, description="Extracted phone numbers")
    phishingLinks: List[str] = Field(default_factory=list, description="Extracted phishing links")
    suspiciousKeywords: List[str] = Field(default_factory=list, description="Detected suspicious keywords")


class SessionData(BaseModel):
    """Model for session data."""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Current confidence score")
    turns: int = Field(default=0, ge=0, description="Number of conversation turns")
    completed: bool = Field(default=False, description="Whether session is completed")
    extracted: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence, description="Extracted intelligence")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last activity time")
    
    # Persona tracking
    current_persona: Optional[str] = Field(default=None, description="Current active persona type")
    persona_history: List[Dict] = Field(default_factory=list, description="History of persona switches")
    
    # Behavior pattern tracking
    behavior_patterns: Dict[str, int] = Field(default_factory=dict, description="Detected scammer behavior patterns")
    message_history: List[str] = Field(default_factory=list, description="Recent message history for pattern detection")
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int) -> bool:
        """
        Check if session is expired.
        
        Args:
            timeout_minutes: Timeout duration in minutes
            
        Returns:
            bool: True if session is expired
        """
        if not self.last_activity:
            return False
        elapsed = (datetime.utcnow() - self.last_activity).total_seconds() / 60
        return elapsed > timeout_minutes


class SessionResponse(BaseModel):
    """Response model for session queries."""
    session_id: str = Field(..., description="Session identifier")
    data: SessionData = Field(..., description="Session data")


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    total: int = Field(..., description="Total number of sessions")
    sessions: List[Dict[str, SessionData]] = Field(..., description="List of sessions")


# -------------------------
# Health Check Models
# -------------------------

class HealthResponse(BaseModel):
    """Basic health check response."""
    status: str = Field(default="healthy", description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""
    status: str = Field(default="healthy", description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
    components: Dict[str, str] = Field(default_factory=dict, description="Component health status")
    metrics: Dict[str, int] = Field(default_factory=dict, description="System metrics")


# -------------------------
# Metrics Models
# -------------------------

class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_sessions: int = Field(default=0, description="Total number of sessions")
    active_sessions: int = Field(default=0, description="Number of active sessions")
    completed_sessions: int = Field(default=0, description="Number of completed sessions")
    total_messages: int = Field(default=0, description="Total messages processed")
    scams_detected: int = Field(default=0, description="Number of scams detected")
    average_confidence: float = Field(default=0.0, description="Average confidence score")
    uptime_seconds: float = Field(default=0.0, description="Server uptime in seconds")


# -------------------------
# Callback Models
# -------------------------

class CallbackPayload(BaseModel):
    """Payload for final callback."""
    sessionId: str = Field(..., description="Session identifier")
    scamDetected: bool = Field(..., description="Whether scam was detected")
    totalMessagesExchanged: int = Field(..., description="Total messages exchanged")
    extractedIntelligence: ExtractedIntelligence = Field(..., description="Extracted intelligence data")
    agentNotes: str = Field(..., description="Agent notes about the interaction")
    finalConfidence: Optional[float] = Field(None, description="Final confidence score")


# -------------------------
# Intelligence Aggregation Models
# -------------------------

class IntelligenceResponse(BaseModel):
    """Response model for aggregated intelligence data."""
    total_sessions: int = Field(..., description="Total number of sessions analyzed")
    scam_sessions: int = Field(..., description="Number of sessions with scam indicators")
    aggregated_intelligence: ExtractedIntelligence = Field(..., description="All extracted intelligence combined")
    unique_counts: Dict[str, int] = Field(..., description="Count of unique items extracted")
    sessions_with_intelligence: List[Dict] = Field(..., description="Sessions that have extracted intelligence")
