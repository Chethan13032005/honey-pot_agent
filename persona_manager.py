"""
Persona Management System for Honey-Pot Agent.
Manages dynamic persona switching to maintain realistic engagement with scammers.
"""
import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PersonaType(str, Enum):
    """Available persona types."""
    CONFUSED_USER = "confused_user"
    NERVOUS_ELDER = "nervous_elder"
    OVER_POLITE = "over_polite"
    TECH_SAVVY = "tech_savvy"


class Persona:
    """Represents a conversation persona with specific characteristics."""
    
    def __init__(
        self,
        name: str,
        persona_type: PersonaType,
        description: str,
        traits: List[str],
        response_style: str,
        min_confidence: float,
        max_confidence: float
    ):
        self.name = name
        self.persona_type = persona_type
        self.description = description
        self.traits = traits
        self.response_style = response_style
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
    
    def get_prompt_context(self) -> str:
        """Generate prompt context for this persona."""
        traits_str = ", ".join(self.traits)
        return f"""
Persona: {self.name}
Characteristics: {traits_str}
Response Style: {self.response_style}

You must embody this persona completely. Your responses should naturally reflect these traits.
"""


# Define available personas
PERSONAS = {
    PersonaType.CONFUSED_USER: Persona(
        name="Confused User",
        persona_type=PersonaType.CONFUSED_USER,
        description="A user who is confused and asks many clarifying questions",
        traits=[
            "easily confused",
            "asks for clarification",
            "repeats information back",
            "uncertain about technical terms",
            "needs step-by-step guidance"
        ],
        response_style="Ask clarifying questions, express confusion about technical terms, request simpler explanations",
        min_confidence=0.7,
        max_confidence=1.0
    ),
    
    PersonaType.NERVOUS_ELDER: Persona(
        name="Nervous Elder",
        persona_type=PersonaType.NERVOUS_ELDER,
        description="An elderly person who is nervous about technology and security",
        traits=[
            "worried about security",
            "not tech-savvy",
            "cautious and hesitant",
            "asks about safety",
            "mentions family members who help with tech"
        ],
        response_style="Express worry and caution, mention needing to ask family, show hesitation about online actions",
        min_confidence=0.5,
        max_confidence=0.7
    ),
    
    PersonaType.OVER_POLITE: Persona(
        name="Over-Polite User",
        persona_type=PersonaType.OVER_POLITE,
        description="An excessively polite user who apologizes frequently",
        traits=[
            "extremely polite",
            "apologizes often",
            "thanks repeatedly",
            "deferential to authority",
            "eager to comply but slow to act"
        ],
        response_style="Be overly polite, apologize for delays, thank profusely, show eagerness to help while being slow",
        min_confidence=0.3,
        max_confidence=0.5
    ),
    
    PersonaType.TECH_SAVVY: Persona(
        name="Tech-Savvy Skeptic",
        persona_type=PersonaType.TECH_SAVVY,
        description="A tech-aware user who is becoming suspicious",
        traits=[
            "asks technical questions",
            "requests verification",
            "mentions security concerns",
            "questions legitimacy subtly",
            "wants official channels"
        ],
        response_style="Ask for verification, mention official websites, express mild skepticism, request documentation",
        min_confidence=0.0,
        max_confidence=0.3
    )
}


class PersonaManager:
    """Manages persona selection and transitions."""
    
    def __init__(self):
        self.personas = PERSONAS
        logger.info("PersonaManager initialized with %d personas", len(self.personas))
    
    def select_persona(self, confidence: float, current_persona: Optional[str] = None) -> Persona:
        """
        Select appropriate persona based on confidence score.
        
        Args:
            confidence: Current confidence score (0.0 to 1.0)
            current_persona: Current persona type (if any)
            
        Returns:
            Selected Persona object
        """
        # Find persona matching confidence range
        for persona_type, persona in self.personas.items():
            if persona.min_confidence <= confidence <= persona.max_confidence:
                # Log if persona changed
                if current_persona and current_persona != persona_type.value:
                    logger.info(
                        f"Persona switching",
                        extra={
                            "from_persona": current_persona,
                            "to_persona": persona_type.value,
                            "confidence": confidence
                        }
                    )
                return persona
        
        # Fallback to confused user if no match
        logger.warning(f"No persona match for confidence {confidence}, using default")
        return self.personas[PersonaType.CONFUSED_USER]
    
    def get_persona_by_type(self, persona_type: str) -> Optional[Persona]:
        """Get persona by type string."""
        try:
            return self.personas[PersonaType(persona_type)]
        except (ValueError, KeyError):
            logger.warning(f"Unknown persona type: {persona_type}")
            return None
    
    def build_persona_prompt(
        self,
        persona: Persona,
        topic: str,
        mode: str,
        scammer_message: str
    ) -> str:
        """
        Build complete prompt with persona context.
        
        Args:
            persona: Persona to use
            topic: Conversation topic
            mode: Behavior mode (NORMAL, DEFLECTION, EXIT)
            scammer_message: The scammer's message
            
        Returns:
            Complete prompt string
        """
        persona_context = persona.get_prompt_context()
        
        # Add mode-specific instructions
        mode_instructions = {
            "NORMAL": "Engage naturally while staying in character.",
            "DEFLECTION": "Show hesitation and ask for time to think or consult someone.",
            "EXIT": "Express intention to handle this through official channels or in person."
        }
        
        mode_instruction = mode_instructions.get(mode, mode_instructions["NORMAL"])
        
        prompt = f"""
{persona_context}

Conversation Context:
- Topic: {topic}
- Current Mode: {mode}
- Mode Instruction: {mode_instruction}

Scammer's Message:
"{scammer_message}"

Important Rules:
1. Stay completely in character as {persona.name}
2. Keep response under 2 short sentences
3. Sound natural and human
4. Do NOT accuse of scam or mention fraud
5. Show the personality traits naturally
6. Ask relevant questions or show appropriate reactions

Generate ONE reply only as {persona.name}:
"""
        return prompt
    
    def get_exit_message(self, persona: Persona, extracted_intelligence: Dict) -> str:
        """
        Generate persona-appropriate exit message.
        
        Args:
            persona: Current persona
            extracted_intelligence: Extracted intelligence data
            
        Returns:
            Natural exit message
        """
        # Persona-specific exit messages
        exit_messages = {
            PersonaType.CONFUSED_USER: [
                "I'm getting too confused. I'll visit the branch directly to sort this out.",
                "This is too complicated for me. I'll go to the office in person tomorrow."
            ],
            PersonaType.NERVOUS_ELDER: [
                "I'm feeling very nervous about this. I'll ask my son to help me at the bank.",
                "This is making me worried. I prefer to handle this face-to-face at the branch."
            ],
            PersonaType.OVER_POLITE: [
                "Thank you so much for your help, but I think I'll visit the branch to be safe. Sorry for the trouble!",
                "I really appreciate your assistance, but I'd feel more comfortable doing this in person. Thank you!"
            ],
            PersonaType.TECH_SAVVY: [
                "I'll verify this through the official website and contact support directly. Thanks.",
                "I prefer to handle this through official channels. I'll call the verified customer service number."
            ]
        }
        
        messages = exit_messages.get(persona.persona_type, exit_messages[PersonaType.CONFUSED_USER])
        
        # Select first message (could be randomized in future)
        return messages[0]


# Global instance
_persona_manager: Optional[PersonaManager] = None


def get_persona_manager() -> PersonaManager:
    """Get or create PersonaManager singleton."""
    global _persona_manager
    if _persona_manager is None:
        _persona_manager = PersonaManager()
    return _persona_manager
