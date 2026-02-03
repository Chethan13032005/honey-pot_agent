import os
import time
import logging
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv
from typing import Optional, Dict

from config import get_settings
from persona_manager import get_persona_manager

load_dotenv()

logger = logging.getLogger(__name__)

# 🔑 STEP 1 — Set Up Gemini
settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)

# Use model from settings
model = genai.GenerativeModel(settings.llm_model)

# Get persona manager
persona_manager = get_persona_manager()

# 🧠 STEP 2 — Decide "MODE"
def decide_mode(confidence):
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if confidence < 0.25:
        return "EXIT"
    elif confidence < 0.5:
        return "DEFLECTION"
    else:
        return "NORMAL"

# 🧠 STEP 3 — Detect Topic
def detect_topic(message):
    msg = message.lower()
    if "fee" in msg or "payment" in msg:
        return "PAYMENT"
    if "otp" in msg:
        return "OTP"
    if "link" in msg or "click" in msg:
        return "LINK"
    if "bank" in msg or "upi" in msg:
        return "BANK"
    return "GENERAL"

# 🤖 STEP 4 — Call Gemini (With Auto-Retry)
def call_llm(prompt):
    """Call LLM with retry mechanism and configured temperature."""
    settings = get_settings()
    
    # Try up to 3 times for Rate Limits OR Connection drops
    for attempt in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.llm_temperature
                )
            )
            return response.text.strip()

        except (exceptions.ResourceExhausted, ConnectionError, Exception) as e:
            # Check if it's a fatal error or a retry-able network error
            error_str = str(e).lower()
            if "quota" in error_str or "connection" in error_str or "remote" in error_str:
                wait_time = 2 * (attempt + 1)
                logger.warning(f"LLM call failed, retrying in {wait_time}s... (attempt {attempt + 1}/3)")
                time.sleep(wait_time)
                continue # Try loop again

            # If it's a real code error (like syntax), print and return fallback
            logger.error(f"LLM error: {e}", exc_info=True)
            return "I'm having trouble understanding. Can you repeat that?"

    return "System busy, please try later."


# 🧩 STEP 5 — FINAL FUNCTION
def generate_reply(
    confidence: float,
    last_message: str = "Hello",
    current_persona: Optional[str] = None,
    extracted_intelligence: Optional[Dict] = None
) -> tuple[str, str]:
    """
    Generate agent reply based on confidence score with persona switching.
    
    Args:
        confidence: Current confidence score (0.0 to 1.0)
        last_message: The last message from scammer
        current_persona: Current persona type (if any)
        extracted_intelligence: Extracted intelligence data
        
    Returns:
        Tuple of (reply text, persona type)
    """
    # Select appropriate persona
    persona = persona_manager.select_persona(confidence, current_persona)
    
    # Detect topic and mode
    topic = detect_topic(last_message)
    mode = decide_mode(confidence)
    
    logger.info(
        f"Generating reply",
        extra={
            "confidence": confidence,
            "mode": mode,
            "topic": topic,
            "persona": persona.persona_type.value,
        }
    )
    
    # Build prompt with persona context
    prompt = persona_manager.build_persona_prompt(
        persona=persona,
        topic=topic,
        mode=mode,
        scammer_message=last_message
    )
    
    # Generate reply
    reply = call_llm(prompt)
    
    return reply, persona.persona_type.value


def generate_exit_message(
    current_persona: Optional[str] = None,
    extracted_intelligence: Optional[Dict] = None
) -> str:
    """
    Generate natural exit message based on persona.
    
    Args:
        current_persona: Current persona type
        extracted_intelligence: Extracted intelligence data
        
    Returns:
        Natural exit message
    """
    # Get current persona or default
    if current_persona:
        persona = persona_manager.get_persona_by_type(current_persona)
    else:
        persona = persona_manager.select_persona(0.2)  # Low confidence persona
    
    if not persona:
        # Fallback exit message
        return "I will visit the bank branch directly. Thank you."
    
    exit_message = persona_manager.get_exit_message(persona, extracted_intelligence or {})
    
    logger.info(
        f"Generated exit message",
        extra={
            "persona": persona.persona_type.value,
            "has_intelligence": bool(extracted_intelligence)
        }
    )
    
    return exit_message

