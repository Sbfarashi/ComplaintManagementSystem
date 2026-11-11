from functools import lru_cache
from pathlib import Path
import re

from joblib import load


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "ml_data"
    / "complaint_classifier.joblib"
)


@lru_cache(maxsize=1)
def load_classifier():
    """Load the locally trained complaint classification model."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Complaint classification model not found: {MODEL_PATH}"
        )

    return load(MODEL_PATH)


def detect_safety_emergency(message):
    """Identify potentially dangerous electrical situations."""
    text = (message or "").lower()

    danger_terms = [
        "electric shock",
        "electrocut",
        "sparking",
        "sparks",
        "smoke",
        "fire",
        "burning smell",
        "burning wire",
        "exposed wire",
        "live wire",
        "electricity leakage",
    ]

    return any(term in text for term in danger_terms)


def classify_complaint(message):
    """Predict the complaint category and model confidence."""
    if not message or not message.strip():
        return {
            "category": "General Complaint",
            "confidence": 0.0,
        }

    model = load_classifier()
    category = str(model.predict([message])[0])

    probabilities = model.predict_proba([message])[0]
    confidence = float(max(probabilities)) * 100

    return {
        "category": category,
        "confidence": round(confidence, 2),
    }


def recommend_priority(message, category=None):
    """Suggest complaint priority using transparent keyword rules."""
    text = (message or "").lower()

    if detect_safety_emergency(text):
        return "High"

    high_terms = [
        "complete outage",
        "no electricity",
        "no power",
        "voltage fluctuation",
        "high voltage",
        "low voltage",
        "meter burning",
        "meter not working",
        "urgent",
        "entire area",
    ]

    if any(term in text for term in high_terms):
        return "High"

    if category in [
        "Meter Fault",
        "Power Outage",
        "Voltage Fluctuation",
        "Meter Replacement",
        "Token Issue",
        "Billing",
        "Installation",
    ]:
        return "Medium"

    return "Low"


def analyze_sentiment(message):
    """Estimate customer sentiment with a simple word-based method."""
    text = (message or "").lower()

    negative_words = [
        "angry", "frustrated", "disappointed", "terrible",
        "poor", "unacceptable", "complain", "failure",
        "worst", "annoyed", "upset", "bad",
    ]

    positive_words = [
        "thank", "thanks", "excellent", "good",
        "satisfied", "appreciate", "helpful", "resolved",
    ]

    negative_score = sum(
        len(re.findall(r"\b" + re.escape(word) + r"\b", text))
        for word in negative_words
    )

    positive_score = sum(
        len(re.findall(r"\b" + re.escape(word) + r"\b", text))
        for word in positive_words
    )

    if negative_score > positive_score:
        return "Negative"

    if positive_score > negative_score:
        return "Positive"

    return "Neutral"


def generate_support_response(message, category=None):
    """Provide guided, rule-based support without a paid API."""
    if detect_safety_emergency(message):
        return (
            "Safety alert: Please stay away from the affected meter, "
            "wires or electrical equipment. Do not touch or attempt to "
            "repair it. Keep other people away and contact the electricity "
            "distribution company or emergency electrical support "
            "immediately. Your complaint should be escalated to a human "
            "support officer."
        )

    if not category:
        category = classify_complaint(message)["category"]

    responses = {
        "Billing": (
            "We can assist with your billing complaint. Please provide "
            "your customer or account number, the affected billing period "
            "and a description of the discrepancy. Do not share your "
            "password or payment PIN."
        ),
        "Meter Fault": (
            "We are sorry about the meter problem. Please describe what "
            "appears on the meter display and whether the meter has power. "
            "Do not open or attempt to repair the meter yourself."
        ),
        "Power Outage": (
            "Please confirm whether the outage affects only your property "
            "or the entire neighbourhood. Include your location and the "
            "time the supply stopped so our support team can investigate."
        ),
        "Installation": (
            "Please provide your installation location, customer details "
            "and the current status of the installation. Our support team "
            "can review the request."
        ),
        "Voltage Fluctuation": (
            "We are sorry about the unstable electricity supply. To protect "
            "your appliances, disconnect sensitive equipment where it is "
            "safe to do so. Please report your location and when the "
            "fluctuation occurs."
        ),
        "Token Issue": (
            "Please confirm when you purchased the token and the error "
            "displayed when you attempted to load it. Never share your "
            "token, payment PIN or account password in this chat."
        ),
        "Meter Replacement": (
            "Please provide your meter number, installation address and "
            "the reason you require a replacement. Our team can assess "
            "your request."
        ),
        "Network Issue": (
            "Please describe the communication or network problem and "
            "provide your meter number and location. Our technical team "
            "may need to investigate."
        ),
        "General Complaint": (
            "Thank you for contacting customer support. Please provide "
            "more details about the problem, your location and any relevant "
            "meter information so we can assist you."
        ),
    }

    return responses.get(
        category,
        "Thank you for contacting us. A support officer can assist "
        "with your complaint."
    )


def analyze_complaint(message):
    """Return the complete automated assessment of a complaint."""
    classification = classify_complaint(message)
    category = classification["category"]

    return {
        "category": category,
        "confidence": classification["confidence"],
        "recommended_priority": recommend_priority(message, category),
        "sentiment": analyze_sentiment(message),
        "safety_alert": detect_safety_emergency(message),
        "support_response": generate_support_response(message, category),
    }
