from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", encoding="utf-8-sig")

from fastapi import FastAPI, HTTPException

from app.models import IntakeRequest
from app.services.ai_service import classify_message
from app.utils.routing import get_route
from app.utils.output import save_record
from app.sample_data import SAMPLE_REQUESTS

app = FastAPI(title="AI Intake Triage API")


@app.get("/")
def root():
    return {"message": "AI Intake API is running"}


@app.post("/api/intake")
async def intake(payload: IntakeRequest):
    try:
        ai_result = await classify_message(payload.source, payload.message)

        route, escalated, reason = get_route(
        ai_result["category"],ai_result["confidence"],payload.message
        )


        record = {
            "source": payload.source,
            "message": payload.message,
            **ai_result,
            "route": route,
            "escalated": escalated,
            "reason": reason,
            "created_at": datetime.now().isoformat(),
        }

        save_record(record)

        return {
            "success": True,
            "data": record,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/intake/sample")
async def process_samples():
    results = []

    for req in SAMPLE_REQUESTS:
        ai_result = await classify_message(req["source"], req["message"])

        route, escalated, reason = get_route(
            ai_result["category"],
            ai_result["confidence"],
            req["message"]
        )

        record = {
            "source": req["source"],
            "message": req["message"],
            **ai_result,
            "route": route,
            "escalated": escalated,
            "reason": reason,
            "created_at": datetime.now().isoformat(),
        }

        save_record(record)
        results.append(record)

    return {
        "success": True,
        "count": len(results),
        "data": results
    }