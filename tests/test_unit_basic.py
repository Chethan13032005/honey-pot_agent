from detection import detect_scam, update_confidence

def test_scam_detection():
    assert detect_scam("Your account is blocked")["is_scam"] is True
    assert detect_scam("Let's meet tomorrow")["is_scam"] is False

def test_confidence_decay():
    c = 1.0
    flags = ["urgency", "keyword:blocked"]
    c = update_confidence(c, flags)
    assert c < 1.0
