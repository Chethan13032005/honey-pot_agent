"""
Integration tests for pass-through mode.
Tests that agent only engages when scam is detected.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from config import get_settings


class TestPassThroughMode:
    """Test pass-through mode functionality."""
    
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)
        self.settings = get_settings()
        self.headers = {"x-api-key": self.settings.api_key}
    
    def test_legitimate_message_passes_through(self):
        """Test that legitimate messages pass through without agent engagement."""
        payload = {
            "sessionId": "test-legit-001",
            "message": {
                "sender": "user",
                "text": "Hello, how are you today?",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        response = self.client.post(
            "/honeypot/message",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Agent should NOT engage
        assert data["agent_engaged"] is False
        assert data["scam_detected"] is False
        assert data["reply"] is None  # No agent reply
        assert data["confidence"] == 1.0  # High confidence (not scam)
        assert data["status"] == "success"
    
    def test_scam_message_triggers_agent(self):
        """Test that scam messages trigger agent engagement."""
        payload = {
            "sessionId": "test-scam-001",
            "message": {
                "sender": "scammer",
                "text": "Your account is blocked! Pay immediately or face legal action!",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        response = self.client.post(
            "/honeypot/message",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Agent SHOULD engage
        assert data["agent_engaged"] is True
        assert data["scam_detected"] is True
        assert data["reply"] is not None  # Agent provides reply
        assert len(data["reply"]) > 0
        assert data["confidence"] < 1.0  # Confidence decreased
        assert data["status"] == "success"
    
    def test_multiple_legitimate_messages(self):
        """Test multiple legitimate messages in sequence."""
        session_id = "test-legit-multi-001"
        
        messages = [
            "Hi there",
            "How's the weather?",
            "Have a great day!"
        ]
        
        for msg in messages:
            payload = {
                "sessionId": session_id,
                "message": {
                    "sender": "user",
                    "text": msg,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            }
            
            response = self.client.post(
                "/honeypot/message",
                json=payload,
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # All should pass through
            assert data["agent_engaged"] is False
            assert data["scam_detected"] is False
            assert data["reply"] is None
    
    def test_scam_after_legitimate_messages(self):
        """Test that agent engages when scam appears after legitimate messages."""
        session_id = "test-mixed-001"
        
        # First, send legitimate message
        legit_payload = {
            "sessionId": session_id,
            "message": {
                "sender": "user",
                "text": "Hello",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        response1 = self.client.post(
            "/honeypot/message",
            json=legit_payload,
            headers=self.headers
        )
        
        assert response1.json()["agent_engaged"] is False
        
        # Then, send scam message
        scam_payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "URGENT: Your account will be suspended! Pay now!",
                "timestamp": "2024-01-01T00:01:00Z"
            }
        }
        
        response2 = self.client.post(
            "/honeypot/message",
            json=scam_payload,
            headers=self.headers
        )
        
        data = response2.json()
        
        # Agent should NOW engage
        assert data["agent_engaged"] is True
        assert data["scam_detected"] is True
        assert data["reply"] is not None
    
    def test_borderline_message(self):
        """Test message with some keywords but not enough to trigger scam."""
        payload = {
            "sessionId": "test-borderline-001",
            "message": {
                "sender": "user",
                "text": "I need to verify my account details",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        response = self.client.post(
            "/honeypot/message",
            json=payload,
            headers=self.headers
        )
        
        data = response.json()
        
        # Should pass through if below scam threshold
        # (depends on scam_confidence_threshold setting)
        assert "agent_engaged" in data
        assert "scam_detected" in data
        assert "reply" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
