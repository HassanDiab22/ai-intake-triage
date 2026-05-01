import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY") or "")


async def classify_message(source: str, message: str) -> dict:
    prompt = f"""
You are an AI intake triage assistant for a B2B software company called ArcVault.

Classify and enrich this inbound request.

Source: {source}
Message: {message}

Return ONLY valid JSON with this exact shape:
{{
  "category": "Bug Report | Feature Request | Billing Issue | Technical Question | Incident/Outage",
  "priority": "Low | Medium | High",
  "confidence": <float between 0.0 and 1.0>,
  "coreIssue": "<one sentence describing the core issue>",
  "identifiers": ["<account IDs, invoice numbers, error codes, URLs, or other specific identifiers found in the message>"],
  "urgencySignal": "Low | Medium | High",
  "summary": "<2-3 sentence human-readable summary for the receiving support team>"
}}

Confidence scoring rules:
- 0.9–1.0: Message clearly and unambiguously fits exactly one category. No interpretation required.
- 0.7–0.89: Message fits one category but has some ambiguity (e.g. could be Bug Report or Incident, or missing context).
- 0.5–0.69: Message is unclear, spans multiple categories, or lacks enough detail to classify reliably.
- 0.0–0.49: Message is too vague, off-topic, or cannot be reliably classified.

Priority rules:
- High: Active outage, data loss, security issue, or blocking a production system.
- Medium: Functional issue with a workaround, billing discrepancy, or integration question.
- Low: Feature request, general question, or non-urgent inquiry.

Urgency signal rules:
- High: Language indicating real-time impact (e.g. "stopped working", "can't log in", "multiple users affected", "right now").
- Medium: Issue exists but there is time to investigate (e.g. invoice error, SSO evaluation).
- Low: Future-looking request or general curiosity.

Extract identifiers only if explicitly present in the message. If none exist, return an empty array.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON. No markdown. No explanation.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise Exception("No response from Groq")

    cleaned = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except Exception:
        raise Exception(f"Invalid JSON from Groq: {cleaned}")