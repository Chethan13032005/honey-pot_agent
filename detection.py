from typing import Dict, List

SCAM_KEYWORDS = [
    "blocked", "suspended", "verify", "urgent", "immediately",
    "account", "upi", "otp", "kyc", "refund", "prize",
    "final", "warning"
]

URGENCY_WORDS = ["now", "today", "immediately", "within", "asap"]
THREAT_WORDS = ["blocked", "suspended", "legal", "terminated"]


def detect_scam(message: str) -> Dict:
    message_lower = message.lower()
    flags: List[str] = []

    for keyword in SCAM_KEYWORDS:
        if keyword in message_lower:
            flags.append(f"keyword:{keyword}")

    if any(word in message_lower for word in URGENCY_WORDS):
        flags.append("urgency")

    if any(word in message_lower for word in THREAT_WORDS):
        flags.append("threat")

    confidence = min(1.0, len(flags) * 0.2)

    return {
        "is_scam": confidence >= 0.4,
        "confidence": round(confidence, 2),
        "flags": flags
    }


def update_confidence(old_confidence: float, flags: List[str]) -> float:
    decay = 0.0

    if "urgency" in flags:
        decay += 0.1

    keyword_count = len([f for f in flags if f.startswith("keyword:")])
    if keyword_count >= 3:
        decay += 0.15

    if "threat" in flags:
        decay += 0.2

    return round(max(0.0, old_confidence - decay), 2)
