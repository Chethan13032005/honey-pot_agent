from detection import detect_scam, update_confidence

confidence = 1.0
messages = [
    "Verify your account",
    "Verify immediately",
    "FINAL WARNING! Account blocked today"
]

for msg in messages:
    result = detect_scam(msg)
    confidence = update_confidence(confidence, result["flags"])
    print(msg, confidence)
