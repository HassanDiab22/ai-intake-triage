# Architecture Write-Up

## System Design

The pipeline is built as a FastAPI application with three distinct layers: ingestion, AI processing, and output. Each layer has a single responsibility and is decoupled from the others.

```
Inbound Request
      │
      ▼
┌─────────────────┐
│   FastAPI        │  POST /api/intake        — single message
│   Endpoints      │  POST /api/intake/sample — all 5 sample inputs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ai_service.py  │  Calls Groq (llama-3.3-70b-versatile)
│   classify_      │  Returns: category, priority, confidence,
│   message()      │  coreIssue, identifiers, urgencySignal, summary
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   routing.py     │  get_route(category, confidence, message)
│   get_route()    │  Returns: (queue_name, escalated: bool)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   output.py      │  Appends full record to output/records.json
│   save_record()  │
└─────────────────┘
         │
         ▼
    JSON Response
    + Persisted Record
```

**Trigger mechanism:** The workflow starts on an HTTP POST request to `/api/intake`. This acts as a webhook receiver — any upstream system (email parser, web form handler, support portal) can trigger it by posting a `source` and `message` field. The `/api/intake/sample` endpoint processes all five test cases in sequence and is used for batch testing.

**State:** There is no in-memory state between requests. Each request is fully self-contained — the message goes in, the enriched record comes out, and it is written to disk. The JSON output file (`output/records.json`) is the only persistent store, acting as both the structured output destination and the audit log.

---

## Routing Logic

Routing is handled entirely in code in `get_route()`, not by the LLM. This is a deliberate architectural decision — routing rules are business logic, not language understanding tasks. Keeping them in code makes them auditable, testable, and easy to change without touching the prompt.

The routing priority order is:

| Priority | Condition                                   | Destination           | Escalated |
| -------- | ------------------------------------------- | --------------------- | --------- |
| 1        | Confidence < 70%                            | Escalation Queue      | true      |
| 2        | Outage keywords in message                  | Escalation Queue      | true      |
| 3        | Category is Incident/Outage                 | Escalation Queue      | true      |
| 4        | Category is Billing Issue AND amount > $500 | Escalation Queue      | true      |
| 5        | Category is Billing Issue (under $500)      | Billing Queue         | false     |
| 6        | Category is Bug Report                      | Engineering Queue     | false     |
| 7        | Category is Feature Request                 | Product Queue         | false     |
| 8        | Category is Technical Question              | IT/Security Queue     | false     |
| 9        | Fallback                                    | General Support Queue | false     |

**Why this order:** Escalation conditions are checked first so that no high-risk message can fall through to a standard queue due to category misclassification. A message about an outage that the model misclassifies as a Bug Report will still escalate because the outage keyword check runs before the category check. This makes the system defensively safe — the routing layer compensates for LLM errors on the most critical cases.

**Billing threshold:** The $500 escalation threshold for billing issues is implemented with a regex extraction of dollar amounts from the raw message. Any billing message containing a dollar amount over $500 is escalated regardless of the model's confidence or priority assignment. This matches the assessment's explicit escalation criterion and ensures large financial discrepancies always receive human review.

---

## Escalation Logic

A record is flagged for human review (`escalated: true`) and routed to the Escalation Queue under four conditions:

1. **Low confidence** — the model's confidence score is below 0.7, meaning the classification is uncertain enough that a human should verify it before it is acted on
2. **Outage language** — the message contains keywords like "outage", "down for all users", or "multiple users affected", regardless of how the model categorized it
3. **Incident/Outage category** — any message the model classifies as an incident is escalated by default, since active outages require immediate human attention
4. **Large billing discrepancy** — any billing message with a dollar amount over $500 is escalated, since financial errors above that threshold carry enough risk to warrant human verification

These four criteria were chosen because they represent the two axes of escalation risk: **uncertainty** (low confidence) and **impact** (outage, security, large billing error). A message can trigger escalation on either axis independently.

---

## What Would Be Done Differently at Production Scale

**Reliability:** The current implementation makes a synchronous Groq API call inside the request handler. If Groq is slow or unavailable, the entire request times out. At scale, this should be replaced with an async message queue (e.g. Redis + Celery, or a managed queue like SQS) so that ingestion is decoupled from processing. The endpoint would accept the message, enqueue it, and return a `202 Accepted` immediately. Processing happens asynchronously and the result is written to a database.

**Storage:** The JSON file output works for a prototype but is not suitable for production. Concurrent writes will corrupt the file, and there is no way to query or filter records. The output layer should be replaced with a proper database (PostgreSQL for structured queries, or a managed option like Supabase) with a row per record and indexed fields for category, route, escalated, and created_at.

**Cost and latency:** `llama-3.3-70b-versatile` on Groq is fast and free-tier accessible, which made it the right choice for this assessment. At production volume, cost per call would need to be monitored. A smaller model (e.g. `llama-3.1-8b-instant`) could handle straightforward classifications at lower cost, with the 70B model reserved for low-confidence cases that need re-evaluation.

**Observability:** There is currently no logging, tracing, or alerting. At production scale, every classification should be logged with its input, output, latency, and confidence score. A confidence distribution dashboard would surface model drift over time — if average confidence starts dropping, it signals that the incoming message patterns have shifted and the prompt or model needs updating.

**Prompt versioning:** The prompt is currently hardcoded in `ai_service.py`. At scale, prompts should be versioned and stored separately so that changes can be A/B tested against each other and rolled back if a new version degrades classification accuracy.

---

## Phase 2 — What Would Be Added With Another Week

**Feedback loop:** Add a `/api/intake/{id}/correct` endpoint that allows support agents to submit the correct category when the model gets it wrong. These corrections would be stored and used to build a labeled dataset for prompt evaluation and eventual fine-tuning.

**Security Incident category:** The current five-category taxonomy has a gap — suspicious login attempts and unauthorized access reports do not fit cleanly into any existing category. A `Security Incident` category would route these directly to IT/Security with escalation, without relying on the downstream keyword matching workaround currently in `get_route()`.

**Multi-issue handling:** Messages that contain two distinct issues (e.g. a billing question and a feature request) currently force the model to pick one and discard the other. Phase 2 would add a `secondaryCategory` field and split such messages into two records, each routed independently.

**Email and web form connectors:** The current ingestion layer accepts only direct API calls. Phase 2 would add a Gmail watcher and a web form webhook so that messages arrive automatically without manual API calls, completing the end-to-end automation loop.

**SLA tagging:** Add an `sla` field to each record based on category and priority (e.g. Incident/High = 1 hour response, Billing/Medium = 24 hours). This gives receiving teams an actionable deadline alongside the classification.
