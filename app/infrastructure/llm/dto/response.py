from pydantic import BaseModel


class LLMResponse(BaseModel):
    response_text: str