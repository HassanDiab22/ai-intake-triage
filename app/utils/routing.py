import re

ESCALATION_KEYWORDS = [
    "outage",
    "down for all users",
    "multiple users affected",
    "all users affected",
]

CATEGORY_ROUTES = {
    "Bug Report": "Engineering Queue",
    "Feature Request": "Product Queue",
    "Technical Question": "IT/Security Queue",
    "Billing Issue": "Billing Queue",
}


def get_route(category: str, confidence: float, message: str) -> tuple[str, bool, str | None]:
    text = message.lower()

    if confidence < 0.7:
        return "Escalation Queue", True, "low_confidence"

    matched_kw = next((kw for kw in ESCALATION_KEYWORDS if kw in text), None)
    if matched_kw:
        return "Escalation Queue", True, f"keyword:{matched_kw}"

    if category == "Incident/Outage":
        return "Escalation Queue", True, "category:incident"

    if category == "Billing Issue":
        amounts = re.findall(r'\$\s*([\d,]+)', message)
        if any(int(amt.replace(",", "")) > 500 for amt in amounts):
            return "Escalation Queue", True, "billing:high_amount"
        return "Billing Queue", False, None

    queue = CATEGORY_ROUTES.get(category, "General Support Queue")
    return queue, False, None