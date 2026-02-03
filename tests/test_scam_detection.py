from detection import detect_scam

TEST_CASES = [
    # (message, expected_is_scam)
    ("Hi, how are you?", False),
    ("Meeting at 5 pm", False),
    ("Let's catch up tomorrow", False),

    ("Your account will be blocked today", True),
    ("Verify immediately to avoid suspension", True),
    ("You won a prize! Click now", True),
    ("Share your UPI ID now", True),
]

def run_tests():
    print("Running scam detection tests...\n")

    for msg, expected in TEST_CASES:
        result = detect_scam(msg)

        print(f"Message: {msg}")
        print(f"Detected: {result['is_scam']} | Expected: {expected}")
        print(f"Confidence: {result['confidence']}")
        print(f"Flags: {result['flags']}")
        print("-" * 50)

        # Soft assertion (won't crash demo runs)
        if result["is_scam"] != expected:
            print("⚠️ Mismatch detected!")

    print("\nScam detection tests completed.")

if __name__ == "__main__":
    run_tests()
