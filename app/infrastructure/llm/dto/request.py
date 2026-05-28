from pydantic import BaseModel
from typing import Optional


class LLMRequest(BaseModel):
    message: list[dict]
    temperature: float
    max_tokens: int
    system: Optional[str] = None