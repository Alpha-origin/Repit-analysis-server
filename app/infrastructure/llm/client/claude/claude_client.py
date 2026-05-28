from anthropic import AsyncAnthropic

from core.config import settings
from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.LLMModel import LLMModel
from infrastructure.llm.dto.request import LLMRequest
from infrastructure.llm.dto.response import LLMResponse


class ClaudeClient(BaseLLMClient):

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        kwargs = dict(
            model=LLMModel.CLAUDE.value,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=request.message,
        )
        if request.system:
            kwargs["system"] = request.system

        response = await self.client.messages.create(**kwargs)
        if response.stop_reason != "end_turn":
            raise Exception(f"unexpected stop reason: {response.stop_reason}")
        return LLMResponse(
            response_text=response.content[0].text,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )