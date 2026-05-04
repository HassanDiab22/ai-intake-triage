def get_prompt(source: str, message: str) -> str:
    """
    Few-Shot prompt — anchors the model with concrete examples before the real input.

    WHY IT'S GOOD:
    - Highest consistency for output shape — the model pattern-matches against
      the examples rather than interpreting abstract rules.
    - Confidence scores become better calibrated because the model has reference
      points to compare against (e.g. 0.97 for a clear outage, 0.95 for a clear
      feature request).
    - Reduces prompt engineering trial-and-error — you fix bad outputs by
      adding or correcting examples rather than rewriting rules.
    - Excellent for enforcing exact field formats without verbose instructions.

    WHEN TO USE:
    - When output consistency is the top priority (e.g. downstream code parses
      the JSON directly with no human review).
    - When confidence score calibration matters (thresholds drive routing logic).
    - When you have real misclassification examples you can turn into corrective
      few-shot cases.
    - Best combined with V4 (Defensive) rules for production use.

    TRADEOFFS:
    - Examples consume significant token budget — 3 examples adds ~300-400 tokens.
    - Can cause the model to over-fit to example patterns, misclassifying tickets
      that don't resemble any example.
    - Example quality directly determines output quality — one bad example
      degrades all outputs.
    """
    return f"""
You are an AI intake triage assistant for ArcVault, a B2B software company.
Classify and enrich inbound support requests. Return ONLY valid JSON.

--- EXAMPLES ---

Source: Email
Message: "Users in our org can't access the dashboard since 9am. Multiple people affected."
Output:
{{
  "category": "Incident/Outage",
  "priority": "High",
  "confidence": 0.97,
  "coreIssue": "Dashboard inaccessible for multiple users since 9am.",
  "identifiers": [],
  "urgencySignal": "High",
  "summary": "Multiple users are unable to access the dashboard as of 9am. This appears to be an active incident affecting the entire organization. Immediate investigation is recommended."
}}

Source: Web Form
Message: "Would be great if we could export reports as CSV. Not urgent."
Output:
{{
  "category": "Feature Request",
  "priority": "Low",
  "confidence": 0.95,
  "coreIssue": "User requests CSV export functionality for reports.",
  "identifiers": [],
  "urgencySignal": "Low",
  "summary": "The customer is requesting a CSV export option for reports. This is a non-urgent feature suggestion with no current workaround mentioned. Suitable for the product backlog."
}}

Source: Support Portal
Message: "Invoice #4421 charged $300 more than our agreed rate."
Output:
{{
  "category": "Billing Issue",
  "priority": "Medium",
  "confidence": 0.93,
  "coreIssue": "Invoice overcharge of $300 compared to contracted rate.",
  "identifiers": ["Invoice #4421"],
  "urgencySignal": "Medium",
  "summary": "The customer reports an overcharge on invoice #4421. The discrepancy is $300 above their agreed rate. The billing team should verify the contract terms and issue a correction if needed."
}}

--- NOW CLASSIFY ---

Source: {source}
Message: {message}

Return ONLY valid JSON with the same shape as the examples above.
""".strip()
