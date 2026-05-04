import re

def get_route(category: str, confidence: float, message: str):
    text = message.lower()

    if confidence <= 1:
        confidence = confidence * 100

    if confidence < 70:
        return "Escalation Queue", True

    if any(kw in text for kw in ["outage", "down for all users", "multiple users affected"]):
        return "Escalation Queue", True

    if category == "Incident/Outage":
        return "Escalation Queue", True

    if category == "Billing Issue":
        amounts = re.findall(r'\$\s*([\d,]+)', message)
        for amt in amounts:
            if int(amt.replace(",", "")) > 500:
                return "Escalation Queue", True
        return "Billing Queue", False

    if category == "Bug Report":
        return "Engineering Queue", False

    if category == "Feature Request":
        return "Product Queue", False

    if category == "Technical Question":
        return "IT/Security Queue", False

    return "General Support Queue", False