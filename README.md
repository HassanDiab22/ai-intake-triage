# AI Intake & Triage Workflow

## How to run

pip install -r requirements.txt
uvicorn app.main:app --reload

## API

POST /api/intake
POST /api/intake/sample

## Notes

- Uses Groq (Llama 3.3 70B)
- Routing logic is deterministic
- Output stored in output/records.json
