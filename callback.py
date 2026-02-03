import requests

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

def send_final_callback(session_id: str, session: dict):
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": session["turns"],
        "extractedIntelligence": session["extracted"],
        "agentNotes": "Scammer used urgency, repetition, and threat escalation"
    }

    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        print("✅ GUVI callback sent successfully")
    except Exception as e:
        print("❌ GUVI callback failed:", e)
