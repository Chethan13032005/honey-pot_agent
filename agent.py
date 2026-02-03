def generate_reply(confidence: float) -> str:
    if confidence > 0.7:
        return "Why is this required now?"
    elif confidence > 0.4:
        return "I already verified once. Why again?"
    else:
        return "I will visit the bank branch directly."
