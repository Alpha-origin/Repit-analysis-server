from pydantic import BaseModel


class LLMResponse(BaseModel):
    response_text: str
    stop_reason: str
    input_tokens: int
    output_tokens: int