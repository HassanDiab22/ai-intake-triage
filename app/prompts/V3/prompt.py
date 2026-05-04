
def get_prompt(source: str, message: str) -> str:
    """
    Minimal / Fast prompt — stripped down to the essential schema only.

    WHY IT'S GOOD:
    - Shortest prompt → lowest token cost and fastest response time.
      Roughly 40% fewer tokens than the original prompt.
    - Works well at high volume (thousands of tickets/day) where latency
      and cost per call matter.
    - Forces reliance on the model's own calibration rather than over-specifying
      rules — good for strong models (GPT-4, Claude Sonnet, Llama 70B).
    - Easiest to maintain — fewer words means fewer places for prompt drift.

    WHEN TO USE:
    - High-volume pipelines where cost and latency are the primary constraints.
    - As a fast pre-filter before a more detailed second-pass prompt on
      low-confidence results.
    - When using a strong frontier model that doesn't need hand-holding.
    - Prototyping and initial testing before adding more structure.

    TRADEOFFS:
    - Less consistent on edge cases and ambiguous tickets vs other versions.
    - Confidence scores are less calibrated — without anchors, the model
      self-calibrates inconsistently across runs.
    - Higher hallucination risk on rare or boundary categories
      (e.g. Bug Report vs Incident/Outage).
    - Not suitable as the sole prompt in a system with no human fallback.
    """
    return f"""
Classify this B2B support request for ArcVault. Return ONLY valid JSON, no explanation.

Source: {source}
Message: {message}

JSON schema:
- category: "Bug Report" | "Feature Request" | "Billing Issue" | "Technical Question" | "Incident/Outage"
- priority: "Low" | "Medium" | "High"  [High=outage/security/data loss, Medium=billing/workaround, Low=feature/question]
- confidence: float 0.0-1.0  [0.9+=clear, 0.7-0.89=some ambiguity, <0.7=unclear]
- coreIssue: string  [one sentence]
- identifiers: string[]  [account IDs, invoice numbers, error codes only — empty array if none]
- urgencySignal: "Low" | "Medium" | "High"  [High=real-time impact, Medium=time to investigate, Low=future]
- summary: string  [2-3 sentences for the receiving team]
""".strip()