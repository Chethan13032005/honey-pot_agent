@echo off
REM ============================================================
REM Honey-Pot API Test Suite (Windows CMD Version)
REM Collection of curl commands to test all endpoints
REM ============================================================

set API_KEY=test_secret_key_12345
set BASE_URL=http://localhost:8000

echo.
echo ============================================================
echo 🧪 Honey-Pot API Test Suite
echo ============================================================
echo.

REM ============================================================
REM 1. HEALTH & INFO ENDPOINTS (No Auth Required)
REM ============================================================

echo 📋 1. Testing Health & Info Endpoints...
echo.

echo 1.1 Basic Health Check:
curl -s %BASE_URL%/health
echo.
echo.

echo 1.2 API Info:
curl -s %BASE_URL%/
echo.
echo.

echo 1.3 Detailed Health Check:
curl -s %BASE_URL%/health/detailed
echo.
echo.

echo 1.4 Metrics:
curl -s %BASE_URL%/metrics
echo.
echo.

REM ============================================================
REM 2. AUTHENTICATION TESTS
REM ============================================================

echo 🔒 2. Testing Authentication...
echo.

echo 2.1 Missing API Key (Should Fail):
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -d "{\"sessionId\":\"auth-test\",\"message\":{\"sender\":\"test\",\"text\":\"hi\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 2.2 Wrong API Key (Should Return 401):
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: wrong_key_123" -d "{\"sessionId\":\"auth-test\",\"message\":{\"sender\":\"test\",\"text\":\"hi\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

REM ============================================================
REM 3. SCAM DETECTION TESTS
REM ============================================================

echo 🎯 3. Testing Scam Detection...
echo.

echo 3.1 Normal Message (No Scam):
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"normal-1\",\"message\":{\"sender\":\"user\",\"text\":\"Hello, how are you today?\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 3.2 Scam with Keywords:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"scam-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Your account is blocked! Pay immediately or it will be suspended!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 3.3 High Urgency Scam:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"scam-2\",\"message\":{\"sender\":\"scammer\",\"text\":\"URGENT! Final warning! Your account will be terminated immediately! Verify now!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

REM ============================================================
REM 4. INTELLIGENCE EXTRACTION TESTS
REM ============================================================

echo 🔍 4. Testing Intelligence Extraction...
echo.

echo 4.1 UPI ID Extraction:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"upi-test-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Send money to scammer@paytm immediately!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 4.2 Phone Number Extraction:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"phone-test-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Call 9876543210 now for urgent verification!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 4.3 URL Extraction:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"url-test-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Click here to verify: https://fake-bank.com/verify urgent!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 4.4 Multiple Intelligence Items:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"multi-intel-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Your account is blocked! Send to fraud@phonepe or call 8765432109. Visit http://malicious-site.com now!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

REM ============================================================
REM 5. MULTI-TURN CONVERSATION TEST
REM ============================================================

echo 💬 5. Testing Multi-Turn Conversation...
echo.

echo 5.1 Turn 1:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"multi-turn-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Your account is blocked!\",\"timestamp\":\"2026-02-03T10:00:00Z\"}}"
echo.
echo.

echo 5.2 Turn 2:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"multi-turn-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Pay immediately or legal action will be taken!\",\"timestamp\":\"2026-02-03T10:01:00Z\"}}"
echo.
echo.

echo 5.3 Turn 3:
curl -s -X POST %BASE_URL%/honeypot/message -H "Content-Type: application/json" -H "x-api-key: %API_KEY%" -d "{\"sessionId\":\"multi-turn-1\",\"message\":{\"sender\":\"scammer\",\"text\":\"Final warning! Account will be suspended now!\",\"timestamp\":\"2026-02-03T10:02:00Z\"}}"
echo.
echo.

REM ============================================================
REM 6. ADMIN ENDPOINTS
REM ============================================================

echo 👤 6. Testing Admin Endpoints...
echo.

echo 6.1 Get Specific Session:
curl -s %BASE_URL%/sessions/scam-1 -H "x-api-key: %API_KEY%"
echo.
echo.

echo 6.2 List All Sessions:
curl -s %BASE_URL%/sessions -H "x-api-key: %API_KEY%"
echo.
echo.

REM ============================================================
REM 7. INTELLIGENCE AGGREGATION
REM ============================================================

echo 🎯 7. Testing Intelligence Aggregation...
echo.

echo 7.1 Get Aggregated Intelligence:
curl -s %BASE_URL%/intelligence -H "x-api-key: %API_KEY%"
echo.
echo.

REM ============================================================
REM SUMMARY
REM ============================================================

echo.
echo ============================================================
echo ✅ Test Suite Complete!
echo ============================================================
echo.
echo 📊 Check the responses above for:
echo   - Status codes (200 OK, 401 Unauthorized, etc.)
echo   - Scam detection confidence scores
echo   - Extracted intelligence (UPI, phone, URLs)
echo   - Session tracking across turns
echo.
echo 📝 Check logs for detailed activity:
echo   type logs\honeypot.log
echo.
echo ============================================================
echo.

pause
