from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict

from detection import detect_scam, update_confidence
from agent import generate_reply
from callback import send_final_callback

app = FastAPI()

# -------------------------
# In-memory session store
# -------------------------
SESSIONS: Dict[str, Dict] = {}

# -------------------------
# Request Models
# -------------------------
class Message(BaseModel):
    sender: str
    text: str
    timestamp: str


class IncomingRequest(BaseModel):
    sessionId: str
    message: Message


# -------------------------
# API Endpoint
# -------------------------
@app.post("/honeypot/message")
def handle_message(
    payload: IncomingRequest,
    x_api_key: str = Header(...)
):
    if x_api_key != "YOUR_SECRET_API_KEY":
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_id = payload.sessionId
    message_text = payload.message.text

    # -------------------------
    # Create or load session
    # -------------------------
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            "confidence": 1.0,
            "turns": 0,
            "completed": False,
            "extracted": {
                "upiIds": [],
                "phoneNumbers": [],
                "phishingLinks": [],
                "suspiciousKeywords": []
            }
        }

    session = SESSIONS[session_id]

    # -------------------------
    # Scam detection
    # -------------------------
    detection = detect_scam(message_text)

    if detection["is_scam"]:
        session["confidence"] = update_confidence(
            session["confidence"],
            detection["flags"]
        )

    session["turns"] += 1

    # -------------------------
    # Stop + Final Callback
    # -------------------------
    if session["confidence"] <= 0.4 and not session["completed"]:
        send_final_callback(session_id, session)
        session["completed"] = True
        reply = "I will visit the bank branch directly."
    else:
        reply = generate_reply(session["confidence"])

    return {
        "status": "success",
        "reply": reply,
        "confidence": session["confidence"]
    }
