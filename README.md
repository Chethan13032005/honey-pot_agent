# Honey-Pot Scam Detection API

AI-powered agentic system that detects scam messages and autonomously engages scammers to extract intelligence.

## 🌟 Features

### 1️⃣ Dynamic Persona Switching
- 4 distinct personas that adapt based on scammer behavior
- Natural conversation flow with realistic responses
- Automatic persona transitions tracked in session history

### 2️⃣ Enhanced Scam Detection
- Repetition detection using similarity matching
- Escalation pattern recognition
- Multi-factor confidence decay algorithm
- Behavior pattern tracking

### 3️⃣ Intelligent Exit Strategy
- Multiple exit conditions (confidence threshold, intelligence collected, max turns)
- Natural persona-appropriate exit messages
- Automatic callback with extracted intelligence

### 4️⃣ Pass-Through Mode
- Monitors all messages silently
- Only engages when scam is detected
- Legitimate messages pass through to user

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```env
# API Security
API_KEY=your-secret-api-key

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key

# Detection Thresholds
SCAM_CONFIDENCE_THRESHOLD=0.4
EXIT_CONFIDENCE_THRESHOLD=0.4
```

### 3. Run the Server

```bash
python main.py
```

Server starts on `http://localhost:8000`

## 📡 API Usage

### Process Message

```bash
curl -X POST http://localhost:8000/honeypot/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "sessionId": "session-123",
    "message": {
      "sender": "user",
      "text": "Your account is blocked!",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'
```

### Response Format

**Legitimate Message:**
```json
{
  "agent_engaged": false,
  "scam_detected": false,
  "reply": null,
  "confidence": 1.0
}
```

**Scam Message:**
```json
{
  "agent_engaged": true,
  "scam_detected": true,
  "reply": "I'm confused. Why is my account blocked?",
  "confidence": 0.7
}
```

### Get Extracted Intelligence

```bash
curl -X GET http://localhost:8000/intelligence \
  -H "x-api-key: your-api-key"
```

Returns all extracted scammer data:
- UPI IDs
- Phone numbers
- Phishing links
- Suspicious keywords

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete setup and deployment instructions
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_persona_manager.py -v
pytest tests/test_detection_enhanced.py -v
pytest tests/test_passthrough.py -v
```

## 🏗️ Architecture

```
honey-pot_project/
├── main.py              # FastAPI application
├── agent.py             # AI agent with persona system
├── persona_manager.py   # Persona management
├── detection.py         # Scam detection & pattern recognition
├── extraction.py        # Intelligence extraction
├── models.py            # Pydantic models
├── config.py            # Configuration management
├── middleware.py        # Custom middleware
├── callback.py          # Callback handling
└── tests/              # Test suite
```

## 🔒 Security

- API key authentication required
- Rate limiting enabled (10 requests/minute)
- Security headers automatically added
- Sensitive data excluded from logs

## 📊 Features in Detail

### Personas

| Persona | Confidence Range | Behavior |
|---------|-----------------|----------|
| Confused User | 0.7 - 1.0 | Asks clarifying questions |
| Nervous Elder | 0.5 - 0.7 | Worried, mentions family |
| Over-Polite | 0.3 - 0.5 | Apologizes frequently |
| Tech-Savvy | 0.0 - 0.3 | Requests verification |

### Confidence Decay Factors

- **Urgency** (-0.10): "now", "immediately", "hurry"
- **Threat** (-0.20): "blocked", "suspended", "legal"
- **Repetition** (-0.10 to -0.20): Scammer repeating messages
- **Escalation** (-0.12 to -0.15): "final warning", repeated pressure
- **Keywords** (-0.08 to -0.15): Multiple scam keywords

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📧 Contact

For questions or support, please open an issue on GitHub.
