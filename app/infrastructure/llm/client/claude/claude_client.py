from anthropic import AsyncAnthropic

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.request import LLMRequest
from infrastructure.llm.dto.response import LLMResponse


class ClaudeClient(BaseLLMClient):

    def __init__(self):
        self.client = AsyncAnthropic(api_key="")

    async def generate(self, model: LLMRequest) -> LLMResponse:
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=model.max_tokens,
            messages=model.prompt
        )
        if not (response.stop_reason == "end_turn"):
            yaho
        return LLMResponse(
            response_text=response.content[0].text
        )