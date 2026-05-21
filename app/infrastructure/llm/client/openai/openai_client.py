from openai import AsyncOpenAI

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.request import LLMRequest
from infrastructure.llm.dto.response import LLMResponse


class OpenAIClient(BaseLLMClient):

    def __init__(self):
        self.client = AsyncOpenAI()

    async def generate(self, request: LLMRequest) -> LLMResponse:
        response = await self.client.completions.create(
            model="gpt-4.1-mini",
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return LLMResponse()