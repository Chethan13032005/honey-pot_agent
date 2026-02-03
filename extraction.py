"""
Enhanced intelligence extraction module.
Extracts UPI IDs, phone numbers, URLs, and other intelligence from messages.
"""
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


# Regex patterns for extraction
UPI_PATTERN = re.compile(
    r'\b[\w\.\-]+@[\w]+\b',  # Matches patterns like user@paytm, name@ybl
    re.IGNORECASE
)

PHONE_PATTERN = re.compile(
    r'\b(?:\+91|91)?[\s\-]?[6-9]\d{9}\b'  # Indian phone numbers
)

URL_PATTERN = re.compile(
    r'https?://(?:www\.)?[\w\-\.]+(?:\.[a-z]{2,})+(?:/[\w\-\./?%&=]*)?',
    re.IGNORECASE
)

# Common UPI providers for validation
UPI_PROVIDERS = [
    'paytm', 'phonepe', 'googlepay', 'ybl', 'oksbi', 'okhdfcbank', 
    'okicici', 'okaxis', 'ibl', 'axl', 'upi'
]


def extract_upi_ids(text: str) -> List[str]:
    """
    Extract UPI IDs from text.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted UPI IDs
    """
    matches = UPI_PATTERN.findall(text)
    
    # Filter to only valid UPI IDs (must have known provider)
    valid_upis = []
    for match in matches:
        # Check if it's a valid UPI ID (has @ and known provider)
        if '@' in match:
            provider = match.split('@')[1].lower()
            # Check if provider is in known list or looks like a bank
            if any(p in provider for p in UPI_PROVIDERS) or 'bank' in provider:
                valid_upis.append(match)
                logger.info(f"Extracted UPI ID: {match}")
    
    return list(set(valid_upis))  # Remove duplicates


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted phone numbers
    """
    matches = PHONE_PATTERN.findall(text)
    
    # Normalize phone numbers (remove spaces, dashes)
    normalized = []
    for match in matches:
        # Remove spaces and dashes
        clean = re.sub(r'[\s\-]', '', match)
        # Remove country code if present
        if clean.startswith('+91'):
            clean = clean[3:]
        elif clean.startswith('91') and len(clean) == 12:
            clean = clean[2:]
        
        if len(clean) == 10:
            normalized.append(clean)
            logger.info(f"Extracted phone number: {clean}")
    
    return list(set(normalized))  # Remove duplicates


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Input text to extract from
        
    Returns:
        List of extracted URLs
    """
    matches = URL_PATTERN.findall(text)
    
    if matches:
        logger.info(f"Extracted {len(matches)} URLs")
    
    return list(set(matches))  # Remove duplicates


def extract_suspicious_keywords(text: str, detected_flags: List[str]) -> List[str]:
    """
    Extract suspicious keywords from detected flags.
    
    Args:
        text: Input text
        detected_flags: List of detection flags
        
    Returns:
        List of suspicious keywords found
    """
    keywords = []
    
    for flag in detected_flags:
        if flag.startswith("keyword:"):
            keyword = flag.replace("keyword:", "")
            keywords.append(keyword)
    
    return list(set(keywords))


def extract_all_intelligence(text: str, detection_flags: List[str] = None) -> Dict[str, List[str]]:
    """
    Extract all intelligence from a message.
    
    Args:
        text: Message text to extract from
        detection_flags: Optional detection flags for keyword extraction
        
    Returns:
        Dictionary containing all extracted intelligence
    """
    intelligence = {
        "upiIds": extract_upi_ids(text),
        "phoneNumbers": extract_phone_numbers(text),
        "phishingLinks": extract_urls(text),
        "suspiciousKeywords": extract_suspicious_keywords(text, detection_flags or [])
    }
    
    # Log summary
    total_items = sum(len(v) for v in intelligence.values())
    if total_items > 0:
        logger.info(
            f"Extracted intelligence summary",
            extra={
                "upi_ids": len(intelligence["upiIds"]),
                "phone_numbers": len(intelligence["phoneNumbers"]),
                "urls": len(intelligence["phishingLinks"]),
                "keywords": len(intelligence["suspiciousKeywords"]),
            }
        )
    
    return intelligence


def merge_intelligence(existing: Dict[str, List[str]], new: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Merge new intelligence with existing intelligence.
    
    Args:
        existing: Existing intelligence dictionary
        new: New intelligence to merge
        
    Returns:
        Merged intelligence dictionary
    """
    merged = {}
    
    for key in ["upiIds", "phoneNumbers", "phishingLinks", "suspiciousKeywords"]:
        # Combine and remove duplicates
        combined = list(set(existing.get(key, []) + new.get(key, [])))
        merged[key] = combined
    
    return merged
