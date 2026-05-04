def get_prompt(source: str, message: str) -> str:
    """
    Chain-of-Thought prompt — forces the model to reason before classifying.

    WHY IT'S GOOD:
    - Reduces hallucination on edge cases by making the model commit to
      reasoning steps before producing the final output.
    - The 'reasoning' field is invaluable for debugging misclassifications
      in production — you can read exactly why the model chose one category
      over another.
    - Handles ambiguous tickets better (e.g. a message that could be both
      a Bug Report and an Incident/Outage).

    WHEN TO USE:
    - During development and debugging when you need to understand model behavior.
    - When classification accuracy matters more than speed or cost.
    - When tickets are complex, multi-topic, or written ambiguously.
    - When you need an audit trail for misclassification reviews.

    TRADEOFFS:
    - ~30-50% more tokens per call vs the minimal prompt → higher cost and latency.
    - The 'reasoning' field adds noise to your structured output and must be
      stripped or stored separately before passing to routing logic.
    """
    return f"""
You are an AI intake triage assistant for ArcVault, a B2B software company.

Source: {source}
Message: {message}

Before classifying, reason through the message step by step:
1. What is the user actually experiencing or asking for?
2. What signals indicate urgency or severity?
3. Which category best fits — and why?
4. Are there any identifiers (account IDs, invoice numbers, error codes)?
5. Could this belong to more than one category? If so, which is primary?

After reasoning, output ONLY this JSON:
{{
  "reasoning": "<your step-by-step analysis in 2-3 sentences>",
  "category": "Bug Report | Feature Request | Billing Issue | Technical Question | Incident/Outage",
  "priority": "Low | Medium | High",
  "confidence": <float 0.0-1.0>,
  "coreIssue": "<one sentence>",
  "identifiers": [],
  "urgencySignal": "Low | Medium | High",
  "summary": "<2-3 sentences for the receiving team>"
}}

Confidence: 0.9+=unambiguous, 0.7-0.89=minor ambiguity, 0.5-0.69=unclear, <0.5=too vague.
Priority: High=active outage/data loss/security. Medium=workaround exists/billing. Low=feature/question.
Urgency: High=real-time impact. Medium=time to investigate. Low=future-looking.
""".strip()
