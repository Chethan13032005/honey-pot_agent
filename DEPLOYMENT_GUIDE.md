# Honey-Pot API Deployment Guide

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Git Bash** or similar terminal (you're on Windows)
3. **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

---

## Step 1: Install Dependencies

Open Git Bash in your project directory and run:

```bash
cd /e/honey-pot_project

# Install all required packages
pip install -r requirements.txt
```

**Required packages:**
- fastapi
- uvicorn
- pydantic
- pydantic-settings
- python-dotenv
- google-generativeai
- requests

---

## Step 2: Configure Environment Variables

Your `.env` file should already exist. Verify it has these settings:

```bash
# View your .env file
cat .env
```

**Required variables:**
```env
# API Security
API_KEY=your-secret-api-key-here

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key-here

# LLM Configuration
LLM_MODEL=models/gemini-1.5-flash-latest
LLM_TEMPERATURE=0.4

# Detection Thresholds
SCAM_CONFIDENCE_THRESHOLD=0.4
EXIT_CONFIDENCE_THRESHOLD=0.4

# Callback URL (optional - for production)
CALLBACK_URL=https://hackathon.guvi.in/api/updateHoneyPotFinalResult

# Environment
ENVIRONMENT=development
DEBUG=true
```

**Important:** Replace `your-gemini-api-key-here` with your actual Gemini API key!

---

## Step 3: Run the API Server

### Option A: Development Mode (Recommended for testing)

```bash
# Run with auto-reload
python main.py
```

This will start the server on `http://0.0.0.0:8000`

### Option B: Production Mode

```bash
# Run with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option C: Custom Port

```bash
# Run on different port (e.g., 8080)
uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## Step 4: Verify API is Running

### Check Health Endpoint

Open a new terminal and run:

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### Access API Documentation

Open your browser and go to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Step 5: Test the API

### Test 1: Legitimate Message (Pass-Through)

```bash
curl -X POST http://localhost:8000/honeypot/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-secret-api-key-here" \
  -d '{
    "sessionId": "test-001",
    "message": {
      "sender": "user",
      "text": "Hello, how are you?",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "reply": null,
  "confidence": 1.0,
  "session_id": "test-001",
  "turns": 0,
  "agent_engaged": false,
  "scam_detected": false
}
```

### Test 2: Scam Message (Agent Engages)

```bash
curl -X POST http://localhost:8000/honeypot/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-secret-api-key-here" \
  -d '{
    "sessionId": "test-002",
    "message": {
      "sender": "scammer",
      "text": "Your account is blocked! Pay immediately or face legal action!",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "reply": "I'm confused. Why is my account blocked?",
  "confidence": 0.7,
  "session_id": "test-002",
  "turns": 1,
  "agent_engaged": true,
  "scam_detected": true
}
```

### Test 3: Use Test Script

```bash
# Run the comprehensive test script
bash test_api.sh
```

---

## API Endpoints

### 1. Health Check
```
GET /health
```
No authentication required.

### 2. Detailed Health Check
```
GET /health/detailed
```
Returns system metrics and component status.

### 3. Process Message (Main Endpoint)
```
POST /honeypot/message
Headers: x-api-key: your-api-key
```

**Request Body:**
```json
{
  "sessionId": "unique-session-id",
  "message": {
    "sender": "sender-id",
    "text": "message text",
    "timestamp": "ISO-8601 timestamp"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "reply": "agent reply or null",
  "confidence": 0.0-1.0,
  "session_id": "session-id",
  "turns": 0,
  "agent_engaged": true/false,
  "scam_detected": true/false
}
```

### 4. Get Aggregated Intelligence
```
GET /intelligence
Headers: x-api-key: your-api-key
```

Returns all extracted scammer data (UPI IDs, phone numbers, URLs).

### 5. Get Session Details
```
GET /sessions/{session_id}
Headers: x-api-key: your-api-key
```

### 6. List All Sessions
```
GET /sessions?limit=100
Headers: x-api-key: your-api-key
```

### 7. Metrics
```
GET /metrics
```

Returns API metrics (sessions, messages, scams detected).

---

## Understanding the Response

### When `agent_engaged: false`
```json
{
  "agent_engaged": false,
  "scam_detected": false,
  "reply": null
}
```
**Meaning:** Legitimate message. Let user handle it.

### When `agent_engaged: true`
```json
{
  "agent_engaged": true,
  "scam_detected": true,
  "reply": "Agent's response",
  "confidence": 0.6
}
```
**Meaning:** Scam detected. Agent is handling with persona.

---

## Integration Example

### Python Client

```python
import requests

API_URL = "http://localhost:8000/honeypot/message"
API_KEY = "your-secret-api-key-here"

def process_message(session_id, sender, text):
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": sender,
            "text": text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    response = requests.post(
        API_URL,
        json=payload,
        headers={"x-api-key": API_KEY}
    )
    
    data = response.json()
    
    if data["agent_engaged"]:
        # Agent is handling - use agent's reply
        print(f"Agent: {data['reply']}")
        print(f"Confidence: {data['confidence']}")
    else:
        # Pass through - show to user
        print(f"User message: {text}")
        print("(No scam detected)")
    
    return data

# Test
process_message("user-123", "user", "Hello!")
process_message("scam-456", "scammer", "Pay now or blocked!")
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000/honeypot/message';
const API_KEY = 'your-secret-api-key-here';

async function processMessage(sessionId, sender, text) {
  const response = await axios.post(API_URL, {
    sessionId: sessionId,
    message: {
      sender: sender,
      text: text,
      timestamp: new Date().toISOString()
    }
  }, {
    headers: {
      'x-api-key': API_KEY,
      'Content-Type': 'application/json'
    }
  });
  
  const data = response.data;
  
  if (data.agent_engaged) {
    console.log(`Agent: ${data.reply}`);
    console.log(`Confidence: ${data.confidence}`);
  } else {
    console.log(`User message: ${text}`);
    console.log('(No scam detected)');
  }
  
  return data;
}
```

---

## Logs

Logs are stored in `logs/honeypot.log`

```bash
# View logs in real-time
tail -f logs/honeypot.log

# View last 50 lines
tail -n 50 logs/honeypot.log

# Search for scam detections
grep "Scam detected" logs/honeypot.log
```

---

## Troubleshooting

### Issue: "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Invalid API key"
- Check your `.env` file has `GEMINI_API_KEY` set
- Verify the API key is valid at https://makersuite.google.com/app/apikey

### Issue: "Port already in use"
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use a different port
uvicorn main:app --port 8080
```

### Issue: "Connection refused"
- Make sure the server is running
- Check firewall settings
- Verify you're using the correct port

---

## Production Deployment

### Using Gunicorn (Linux/Mac)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t honeypot-api .
docker run -p 8000:8000 --env-file .env honeypot-api
```

### Environment Variables for Production

```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=10
```

---

## Security Notes

1. **Change API Key**: Use a strong, unique API key in production
2. **HTTPS**: Use HTTPS in production (not HTTP)
3. **Rate Limiting**: Enabled by default (10 requests/minute)
4. **CORS**: Configure `ALLOWED_ORIGINS` in `.env` for production
5. **API Docs**: Disabled in production (set `DEBUG=false`)

---

## Next Steps

1. ✅ Start the server: `python main.py`
2. ✅ Test with curl or Postman
3. ✅ Integrate with your application
4. ✅ Monitor logs for scam detections
5. ✅ Check `/intelligence` endpoint for collected data

**Your honey-pot API is ready! 🎉**
