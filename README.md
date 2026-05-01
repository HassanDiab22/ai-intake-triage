# AI Intake & Triage Workflow

An AI-powered workflow that processes unstructured inbound requests, classifies and enriches them using an LLM, and routes them to the appropriate team with escalation for high-risk cases.

---

## 🚀 How to Run

### 1. Install dependencies

pip install -r requirements.txt

---

### 2. Add your Groq API key

Create a .env file in the project root and add:

GROQ_API_KEY=your_groq_api_key_here

---

### 3. Run the server

uvicorn app.main:app --reload

---

## 📡 API Endpoints

- POST /api/intake  
  Process a single inbound request

- POST /api/intake/sample  
  Process all sample inputs (for demo/testing)

---

## 🧠 How It Works

1. Ingestion  
   Accepts inbound messages via API (simulating email, web forms, or support portals)

2. AI Processing  
   Uses Groq (Llama 3.3 70B) to:
   - classify the request
   - assign priority
   - extract identifiers
   - generate a summary

3. Routing Logic  
   Deterministic rules (not AI) decide:
   - destination queue (Engineering, Product, Billing, etc.)
   - escalation for high-risk cases

4. Output  
   Each request is saved as a structured record in:
   output/records.json

---

## ⚙️ Key Design Decisions

- LLM for understanding, code for decisions  
  AI handles classification, while routing and escalation are implemented in code for consistency and reliability.

- Escalation-first logic  
  Critical cases (low confidence, outages, large billing issues) override normal routing.

- Single-step AI call  
  Classification and enrichment are combined into one call to reduce latency and cost.

---

## 📄 Notes

- Uses Groq (Llama 3.3 70B) for fast and cost-efficient inference
- Confidence is normalized (0–1 → 0–100) before routing decisions
- Output is stored locally as JSON for simplicity (prototype design)
