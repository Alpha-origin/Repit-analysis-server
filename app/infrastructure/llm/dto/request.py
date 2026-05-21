from pydantic import BaseModel


class LLMRequest(BaseModel):
    prompt: str
    temperature: float
    max_tokens: int