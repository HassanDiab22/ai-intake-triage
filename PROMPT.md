# Prompt Documentation

## The Prompt

```
You are an AI intake triage assistant for a B2B software company called ArcVault.

Classify and enrich this inbound request.

Source: {source}
Message: {message}

Return ONLY valid JSON with this exact shape:
{
  "category": "Bug Report | Feature Request | Billing Issue | Technical Question | Incident/Outage",
  "priority": "Low | Medium | High",
  "confidence": <float between 0.0 and 1.0>,
  "coreIssue": "<one sentence describing the core issue>",
  "identifiers": ["<account IDs, invoice numbers, error codes, URLs, or other specific identifiers>"],
  "urgencySignal": "Low | Medium | High",
  "summary": "<2-3 sentence human-readable summary for the receiving support team>"
}

Note: Confidence is normalized to a 0–100 scale before being used in routing logic (e.g., 0.8 → 80%).

Confidence scoring rules:
- 0.9–1.0: Message clearly and unambiguously fits exactly one category. No interpretation required.
- 0.7–0.89: Message fits one category but has some ambiguity.
- 0.5–0.69: Message is unclear, spans multiple categories, or lacks enough detail.
- 0.0–0.49: Message is too vague, off-topic, or cannot be reliably classified.

Priority rules:
- High: Active outage, data loss, security issue, or blocking a production system.
- Medium: Functional issue with a workaround, billing discrepancy, or integration question.
- Low: Feature request, general question, or non-urgent inquiry.

Urgency signal rules:
- High: Language indicating real-time impact (e.g. "stopped working", "can't log in", "multiple users affected").
- Medium: Issue exists but there is time to investigate (e.g. invoice error, SSO evaluation).
- Low: Future-looking request or general curiosity.

Extract identifiers only if explicitly present in the message. If none exist, return an empty array.
```

---

## Why It Was Structured This Way

### Single-step classification and enrichment

The prompt combines classification, enrichment, and summarization into one LLM call rather than chaining separate prompts for each step. This reduces latency, lowers API cost, and avoids compounding errors across multiple calls — if the first call misclassifies, a second call built on top of it inherits that mistake. Since all required fields are closely related (category informs priority, which informs urgency), a single-context call produces more internally consistent output.

### Strict JSON-only output with a schema

The system message instructs the model to return only valid JSON with no markdown or explanation, and the prompt defines the exact field names and value types. This removes the need for fragile regex parsing and makes the output directly deserializable. The schema also acts as a constraint — by showing the model the expected shape upfront, it is less likely to invent fields or omit required ones. A `temperature` of `0.2` was chosen to reduce output variance and improve consistency across calls, making the responses more deterministic and less likely to deviate from the defined schema.

### Explicit confidence scoring rubric

Early versions of the prompt returned `confidence: 0.8` for nearly every message regardless of actual ambiguity. The fix was to define confidence not as a feeling but as a rule set tied to specific conditions: whether the message fits exactly one category, whether context is missing, or whether the message is too vague to classify at all. This transforms confidence from a decorative field into a functional signal that drives routing decisions — messages below 0.7 are automatically sent to the Escalation Queue for human review.

### Separate priority and urgency signal fields

`priority` and `urgencySignal` are intentionally kept as separate fields. Priority reflects the objective severity of the issue (what kind of problem is it), while urgency reflects the customer's subjective tone and time pressure (how urgent do they feel it is). These two dimensions do not always align — a billing discrepancy is medium priority but may carry high urgency if the customer is angry. Keeping them separate gives the receiving team more signal to act on, and avoids flattening two distinct dimensions into one field.

### Identifier extraction with explicit constraints

The prompt instructs the model to extract identifiers only if they are explicitly present in the message, and to return an empty array otherwise. Without this constraint, the model tends to hallucinate plausible-sounding identifiers (account names, invoice numbers) when none exist in the source text. The constraint prevents this and keeps the output auditable — every identifier in the output can be traced directly to the original message.

---

## Tradeoffs Made

**Single call vs. multi-step chain:** A chained approach where classification happens first and enrichment second would allow each step to be optimized independently, but adds latency and cost per message. For this use case, the single-call approach is the right tradeoff given the volume and the tight coupling between fields.

**Fixed category set:** The five categories cover the majority of inbound request types but leave gaps — security incidents (unrecognized login attempts, suspicious activity) do not fit cleanly into any category. They currently land in `Incident/Outage` or `Technical Question` depending on phrasing, with routing corrected downstream via keyword matching in `get_route`. A `Security Incident` category would be the right fix with more time.

**LLM confidence as a signal, not a guarantee:** The confidence score is the model's self-reported certainty, not a statistically calibrated probability. It is useful as a routing signal but should not be treated as ground truth. At production scale, confidence scores should be validated against human-reviewed labels to determine whether the model's self-assessment is actually correlated with classification accuracy.

---

## What Would Change With More Time

- Add a `Security Incident` category to handle suspicious login and access anomaly reports cleanly without relying on downstream keyword matching
- Add few-shot examples directly in the prompt for the two most ambiguous cases: single-user login failures (Bug Report vs. Incident/Outage) and pre-sales feature questions (Feature Request vs. Technical Question)
- Run the prompt against a larger labeled dataset and tune the confidence rubric thresholds based on actual model behavior rather than intuition
- Add a `secondaryCategory` field to handle multi-issue messages without forcing the model to discard half the information
