from openai import AsyncOpenAI

from app.core.config import settings
from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.dto.LLMModel import LLMModel
from app.infrastructure.llm.dto.request import LLMRequest
from app.infrastructure.llm.dto.response import LLMResponse


class OpenAIClient(BaseLLMClient):

    def __init__(self):
        if not settings.OPENAI_API_KEY.strip():
            raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
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
        choice = self._get_first_choice(response.choices)
        if choice.finish_reason != "stop":
            raise RuntimeError(f"OpenAI 응답이 정상 종료되지 않았습니다: {choice.finish_reason}")

        response_text = self._extract_response_text(choice.message.content)
        input_tokens, output_tokens = self._extract_usage(response.usage)
        return LLMResponse(
            response_text=response_text,
            stop_reason=choice.finish_reason,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    @staticmethod
    def _get_first_choice(choices: list):
        if not choices:
            raise RuntimeError("OpenAI 응답에 선택 결과가 없습니다.")
        return choices[0]

    @staticmethod
    def _extract_response_text(content: str | None) -> str:
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenAI 응답에 유효한 텍스트 본문이 없습니다.")
        return content.strip()

    @staticmethod
    def _extract_usage(usage) -> tuple[int, int]:
        if usage is None:
            return 0, 0
        return (
            getattr(usage, "prompt_tokens", 0) or 0,
            getattr(usage, "completion_tokens", 0) or 0,
        )
