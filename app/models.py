from pydantic import BaseModel
from typing import List, Optional


class IntakeRequest(BaseModel):
    source: Optional[str] = "Unknown"
    message: str


class IntakeResponse(BaseModel):
    success: bool
    data: dict