from openai import AsyncOpenAI

from core.config import settings
from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.LLMModel import LLMModel
from infrastructure.llm.dto.request import LLMRequest
from infrastructure.llm.dto.response import LLMResponse


class OpenAIClient(BaseLLMClient):

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        messages = request.message
        if request.system:
            messages = [{"role": "system", "content": request.system}] + messages

        response = await self.client.chat.completions.create(
            model=LLMModel.GPT.value,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        choice = response.choices[0]
        if choice.finish_reason != "stop":
            raise Exception(f"unexpected finish reason: {choice.finish_reason}")
        return LLMResponse(
            response_text=choice.message.content,
            stop_reason=choice.finish_reason,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )