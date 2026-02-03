"""
Unit tests for persona manager functionality.
"""
import pytest
from persona_manager import PersonaManager, PersonaType, get_persona_manager


class TestPersonaManager:
    """Test suite for PersonaManager."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.manager = PersonaManager()
    
    def test_persona_selection_high_confidence(self):
        """Test persona selection at high confidence (0.8-1.0)."""
        persona = self.manager.select_persona(0.9)
        assert persona.persona_type == PersonaType.CONFUSED_USER
        assert 0.7 <= persona.min_confidence <= 0.9
        assert persona.max_confidence >= 0.9
    
    def test_persona_selection_medium_confidence(self):
        """Test persona selection at medium confidence (0.5-0.7)."""
        persona = self.manager.select_persona(0.6)
        assert persona.persona_type == PersonaType.NERVOUS_ELDER
        assert persona.min_confidence <= 0.6
        assert persona.max_confidence >= 0.6
    
    def test_persona_selection_low_confidence(self):
        """Test persona selection at low confidence (0.3-0.5)."""
        persona = self.manager.select_persona(0.4)
        assert persona.persona_type == PersonaType.OVER_POLITE
        assert persona.min_confidence <= 0.4
        assert persona.max_confidence >= 0.4
    
    def test_persona_selection_very_low_confidence(self):
        """Test persona selection at very low confidence (0.0-0.3)."""
        persona = self.manager.select_persona(0.2)
        assert persona.persona_type == PersonaType.TECH_SAVVY
        assert persona.min_confidence <= 0.2
        assert persona.max_confidence >= 0.2
    
    def test_persona_switching_detection(self, caplog):
        """Test that persona switching is logged."""
        # First selection
        persona1 = self.manager.select_persona(0.9, None)
        
        # Second selection with different confidence
        persona2 = self.manager.select_persona(0.4, persona1.persona_type.value)
        
        # Should have switched personas
        assert persona1.persona_type != persona2.persona_type
    
    def test_build_persona_prompt(self):
        """Test prompt building with persona context."""
        persona = self.manager.select_persona(0.6)
        prompt = self.manager.build_persona_prompt(
            persona=persona,
            topic="PAYMENT",
            mode="NORMAL",
            scammer_message="Pay immediately"
        )
        
        # Check prompt contains key elements
        assert persona.name in prompt
        assert "PAYMENT" in prompt
        assert "NORMAL" in prompt
        assert "Pay immediately" in prompt
    
    def test_exit_message_generation(self):
        """Test exit message generation for different personas."""
        # Test for each persona type
        for persona_type in PersonaType:
            persona = self.manager.personas[persona_type]
            exit_msg = self.manager.get_exit_message(persona, {})
            
            # Exit message should not be empty
            assert len(exit_msg) > 0
            # Should be a reasonable length
            assert len(exit_msg) < 200
    
    def test_get_persona_by_type(self):
        """Test retrieving persona by type string."""
        persona = self.manager.get_persona_by_type("confused_user")
        assert persona is not None
        assert persona.persona_type == PersonaType.CONFUSED_USER
    
    def test_get_persona_by_invalid_type(self):
        """Test retrieving persona with invalid type."""
        persona = self.manager.get_persona_by_type("invalid_type")
        assert persona is None
    
    def test_singleton_pattern(self):
        """Test that get_persona_manager returns singleton."""
        manager1 = get_persona_manager()
        manager2 = get_persona_manager()
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
