from typing import Dict, List
import logging
from difflib import SequenceMatcher

from config import get_settings

logger = logging.getLogger(__name__)

SCAM_KEYWORDS = [
    "blocked", "suspended", "verify", "urgent", "immediately",
    "account", "upi", "otp", "kyc", "refund", "prize",
    "final", "warning", "expire", "deactivate", "confirm"
]

URGENCY_WORDS = ["now", "today", "immediately", "within", "asap", "hurry", "quick", "fast"]
THREAT_WORDS = ["blocked", "suspended", "legal", "terminated", "action", "penalty", "fine"]
ESCALATION_WORDS = ["final", "last", "ultimate", "warning", "chance"]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def detect_repetition(message: str, message_history: List[str], threshold: float = 0.7) -> Dict:
    """
    Detect if message is repetitive compared to history.
    
    Args:
        message: Current message
        message_history: List of previous messages
        threshold: Similarity threshold to consider repetition
        
    Returns:
        Dictionary with repetition detection results
    """
    if not message_history:
        return {"is_repetitive": False, "similarity": 0.0, "repeated_count": 0}
    
    # Check similarity with recent messages (last 5)
    recent_messages = message_history[-5:]
    max_similarity = 0.0
    repeated_count = 0
    
    for prev_message in recent_messages:
        similarity = calculate_similarity(message, prev_message)
        max_similarity = max(max_similarity, similarity)
        
        if similarity >= threshold:
            repeated_count += 1
    
    is_repetitive = max_similarity >= threshold
    
    if is_repetitive:
        logger.info(
            f"Repetitive message detected",
            extra={
                "similarity": round(max_similarity, 2),
                "repeated_count": repeated_count,
                "threshold": threshold
            }
        )
    
    return {
        "is_repetitive": is_repetitive,
        "similarity": round(max_similarity, 2),
        "repeated_count": repeated_count
    }


def detect_escalation(message: str, behavior_patterns: Dict[str, int]) -> Dict:
    """
    Detect escalation patterns in scammer behavior.
    
    Args:
        message: Current message
        behavior_patterns: Dictionary tracking behavior pattern counts
        
    Returns:
        Dictionary with escalation detection results
    """
    message_lower = message.lower()
    escalation_detected = False
    escalation_type = None
    
    # Check for escalation keywords
    has_escalation_words = any(word in message_lower for word in ESCALATION_WORDS)
    
    # Check for increasing urgency
    urgency_count = behavior_patterns.get("urgency", 0)
    threat_count = behavior_patterns.get("threat", 0)
    
    # Escalation if multiple threats or urgency messages
    if urgency_count >= 2 or threat_count >= 2:
        escalation_detected = True
        escalation_type = "repeated_pressure"
    
    # Escalation if using "final warning" type language
    if has_escalation_words:
        escalation_detected = True
        escalation_type = "final_warning"
    
    if escalation_detected:
        logger.warning(
            f"Escalation pattern detected",
            extra={
                "escalation_type": escalation_type,
                "urgency_count": urgency_count,
                "threat_count": threat_count
            }
        )
    
    return {
        "is_escalating": escalation_detected,
        "escalation_type": escalation_type,
        "urgency_count": urgency_count,
        "threat_count": threat_count
    }


def detect_scam(message: str, message_history: List[str] = None, behavior_patterns: Dict[str, int] = None) -> Dict:
    """
    Detect scam indicators in a message with enhanced pattern detection.
    
    Args:
        message: Message text to analyze
        message_history: Optional list of previous messages for repetition detection
        behavior_patterns: Optional behavior pattern tracking
        
    Returns:
        Dictionary with detection results
    """
    settings = get_settings()
    message_lower = message.lower()
    flags: List[str] = []
    
    # Initialize optional parameters
    if message_history is None:
        message_history = []
    if behavior_patterns is None:
        behavior_patterns = {}

    # Keyword detection
    for keyword in SCAM_KEYWORDS:
        if keyword in message_lower:
            flags.append(f"keyword:{keyword}")

    # Urgency detection
    if any(word in message_lower for word in URGENCY_WORDS):
        flags.append("urgency")

    # Threat detection
    if any(word in message_lower for word in THREAT_WORDS):
        flags.append("threat")
    
    # Repetition detection
    repetition_result = detect_repetition(message, message_history)
    if repetition_result["is_repetitive"]:
        flags.append(f"repetition:{repetition_result['similarity']}")
    
    # Escalation detection
    escalation_result = detect_escalation(message, behavior_patterns)
    if escalation_result["is_escalating"]:
        flags.append(f"escalation:{escalation_result['escalation_type']}")

    confidence = min(1.0, len(flags) * 0.2)
    is_scam = confidence >= settings.scam_confidence_threshold
    
    if is_scam:
        logger.warning(
            f"Scam detected in message",
            extra={
                "confidence": round(confidence, 2),
                "flags": flags,
                "threshold": settings.scam_confidence_threshold,
                "message_preview": message[:50] + "..." if len(message) > 50 else message
            }
        )

    return {
        "is_scam": is_scam,
        "confidence": round(confidence, 2),
        "flags": flags,
        "repetition": repetition_result,
        "escalation": escalation_result
    }


def update_confidence(old_confidence: float, flags: List[str], repetition_data: Dict = None, escalation_data: Dict = None) -> float:
    """
    Update confidence score with enhanced decay based on scammer behavior.
    
    Args:
        old_confidence: Previous confidence score
        flags: Detection flags
        repetition_data: Repetition detection results
        escalation_data: Escalation detection results
        
    Returns:
        Updated confidence score
    """
    decay = 0.0

    # Base decay for urgency
    if "urgency" in flags:
        decay += 0.1

    # Keyword-based decay
    keyword_count = len([f for f in flags if f.startswith("keyword:")])
    if keyword_count >= 3:
        decay += 0.15
    elif keyword_count >= 2:
        decay += 0.08

    # Threat-based decay
    if "threat" in flags:
        decay += 0.2
    
    # Repetition-based decay (scammer repeating same message)
    if repetition_data and repetition_data.get("is_repetitive"):
        similarity = repetition_data.get("similarity", 0.0)
        repeated_count = repetition_data.get("repeated_count", 0)
        
        # Higher decay for more repetition
        decay += 0.1 * similarity
        if repeated_count >= 2:
            decay += 0.1  # Extra penalty for multiple repetitions
    
    # Escalation-based decay (scammer getting aggressive)
    if escalation_data and escalation_data.get("is_escalating"):
        escalation_type = escalation_data.get("escalation_type")
        
        if escalation_type == "final_warning":
            decay += 0.15  # Strong signal of scam
        elif escalation_type == "repeated_pressure":
            decay += 0.12
    
    new_confidence = round(max(0.0, old_confidence - decay), 2)
    
    logger.info(
        f"Confidence updated",
        extra={
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "decay": round(decay, 2),
            "flags": flags
        }
    )

    return new_confidence
