from anthropic import AsyncAnthropic

from app.core.config import settings
from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.dto.LLMModel import LLMModel
from app.infrastructure.llm.dto.request import LLMRequest
from app.infrastructure.llm.dto.response import LLMResponse


class ClaudeClient(BaseLLMClient):

    def __init__(self):
        if not settings.CLAUDE_API_KEY.strip():
            raise ValueError("CLAUDE_API_KEY 환경변수가 설정되지 않았습니다.")
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

        response_text = self._extract_response_text(response.content)
        return LLMResponse(
            response_text=response_text,
            stop_reason=response.stop_reason,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    @staticmethod
    def _extract_response_text(content: list) -> str:
        text_blocks = [
            block.text.strip()
            for block in content
            if getattr(block, "type", None) == "text"
            and isinstance(getattr(block, "text", None), str)
            and block.text.strip()
        ]
        if not text_blocks:
            raise RuntimeError("Claude 응답에 유효한 텍스트 본문이 없습니다.")
        return "\n".join(text_blocks)
