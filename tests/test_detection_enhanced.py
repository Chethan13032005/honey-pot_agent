"""
Unit tests for enhanced detection functionality.
"""
import pytest
from detection import (
    detect_scam, update_confidence, detect_repetition,
    detect_escalation, calculate_similarity
)


class TestSimilarityCalculation:
    """Test similarity calculation."""
    
    def test_identical_messages(self):
        """Test similarity of identical messages."""
        similarity = calculate_similarity("Hello world", "Hello world")
        assert similarity == 1.0
    
    def test_completely_different_messages(self):
        """Test similarity of completely different messages."""
        similarity = calculate_similarity("Hello", "Goodbye")
        assert similarity < 0.5
    
    def test_similar_messages(self):
        """Test similarity of similar messages."""
        similarity = calculate_similarity(
            "Pay immediately or account blocked",
            "Pay now or your account will be blocked"
        )
        assert similarity > 0.5


class TestRepetitionDetection:
    """Test repetition detection."""
    
    def test_no_repetition_empty_history(self):
        """Test with empty message history."""
        result = detect_repetition("Hello", [])
        assert result["is_repetitive"] is False
        assert result["similarity"] == 0.0
    
    def test_repetition_detected(self):
        """Test repetition detection with similar messages."""
        history = [
            "Pay immediately",
            "Send OTP now",
            "Pay immediately or blocked"
        ]
        result = detect_repetition("Pay immediately", history)
        assert result["is_repetitive"] is True
        assert result["similarity"] >= 0.7
    
    def test_no_repetition_different_messages(self):
        """Test no repetition with different messages."""
        history = [
            "Hello",
            "How are you",
            "What is your name"
        ]
        result = detect_repetition("Pay immediately", history)
        assert result["is_repetitive"] is False


class TestEscalationDetection:
    """Test escalation pattern detection."""
    
    def test_escalation_final_warning(self):
        """Test escalation with final warning keywords."""
        result = detect_escalation(
            "This is your final warning",
            {"urgency": 1, "threat": 1}
        )
        assert result["is_escalating"] is True
        assert result["escalation_type"] == "final_warning"
    
    def test_escalation_repeated_pressure(self):
        """Test escalation with repeated urgency."""
        result = detect_escalation(
            "Pay now",
            {"urgency": 3, "threat": 1}
        )
        assert result["is_escalating"] is True
        assert result["escalation_type"] == "repeated_pressure"
    
    def test_no_escalation(self):
        """Test no escalation detected."""
        result = detect_escalation(
            "Hello",
            {"urgency": 0, "threat": 0}
        )
        assert result["is_escalating"] is False


class TestScamDetection:
    """Test enhanced scam detection."""
    
    def test_basic_scam_detection(self):
        """Test basic scam keyword detection."""
        result = detect_scam("Your account is blocked. Pay immediately.")
        assert result["is_scam"] is True
        assert len(result["flags"]) > 0
    
    def test_scam_with_repetition(self):
        """Test scam detection with repetition."""
        history = ["Pay now", "Pay immediately"]
        result = detect_scam(
            "Pay now",
            message_history=history,
            behavior_patterns={"urgency": 1}
        )
        assert result["is_scam"] is True
        assert result["repetition"]["is_repetitive"] is True
    
    def test_scam_with_escalation(self):
        """Test scam detection with escalation."""
        result = detect_scam(
            "Final warning: pay now",
            message_history=[],
            behavior_patterns={"urgency": 2, "threat": 2}
        )
        assert result["is_scam"] is True
        assert result["escalation"]["is_escalating"] is True
    
    def test_no_scam_detected(self):
        """Test legitimate message."""
        result = detect_scam("Hello, how can I help you?")
        assert result["is_scam"] is False


class TestConfidenceUpdate:
    """Test confidence score updates."""
    
    def test_basic_confidence_decay(self):
        """Test basic confidence decay with urgency."""
        new_confidence = update_confidence(
            1.0,
            ["urgency", "keyword:blocked"]
        )
        assert new_confidence < 1.0
    
    def test_confidence_decay_with_repetition(self):
        """Test confidence decay with repetition."""
        repetition_data = {
            "is_repetitive": True,
            "similarity": 0.9,
            "repeated_count": 2
        }
        new_confidence = update_confidence(
            0.8,
            ["urgency"],
            repetition_data=repetition_data
        )
        # Should have significant decay
        assert new_confidence < 0.6
    
    def test_confidence_decay_with_escalation(self):
        """Test confidence decay with escalation."""
        escalation_data = {
            "is_escalating": True,
            "escalation_type": "final_warning"
        }
        new_confidence = update_confidence(
            0.7,
            ["threat"],
            escalation_data=escalation_data
        )
        # Should have significant decay
        assert new_confidence < 0.5
    
    def test_confidence_minimum_zero(self):
        """Test confidence doesn't go below zero."""
        new_confidence = update_confidence(
            0.1,
            ["urgency", "threat", "keyword:blocked"],
            repetition_data={"is_repetitive": True, "similarity": 0.9, "repeated_count": 3},
            escalation_data={"is_escalating": True, "escalation_type": "final_warning"}
        )
        assert new_confidence >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
