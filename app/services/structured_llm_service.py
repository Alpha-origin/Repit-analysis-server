import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.request import LLMRequest

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class StructuredLLMService:
    def __init__(self, llm_client: BaseLLMClient):
        self._llm_client = llm_client

    async def generate_structured_output(
        self,
        response_model: type[T],
        messages: list[dict],
        system_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        max_attempts: int = 3,
    ) -> T:
        if max_attempts < 1:
            raise ValueError("max_attempts는 1 이상이어야 합니다.")

        request_messages = [dict(message) for message in messages]
        last_error: ValidationError | None = None

        for attempt in range(1, max_attempts + 1):
            request = LLMRequest(
                message=request_messages,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            response = await self._llm_client.generate(request)
            text = self._strip_code_fence(response.response_text)

            try:
                return response_model.model_validate_json(text)
            except ValidationError as exc:
                last_error = exc
                logger.warning(
                    "structured LLM response validation failed model=%s attempt=%s/%s",
                    response_model.__name__,
                    attempt,
                    max_attempts,
                )
                if attempt == max_attempts:
                    break

                request_messages.extend(
                    [
                        {
                            "role": "assistant",
                            "content": response.response_text,
                        },
                        {
                            "role": "user",
                            "content": self._build_retry_prompt(response_model, exc),
                        },
                    ]
                )

        raise ValueError(
            f"LLM 응답을 {response_model.__name__} 스키마로 변환하지 못했습니다. "
            f"총 {max_attempts}회 시도했습니다: {last_error}"
        ) from last_error

    @staticmethod
    def _build_retry_prompt(
        response_model: type[BaseModel],
        validation_error: ValidationError,
    ) -> str:
        schema = json.dumps(
            response_model.model_json_schema(),
            ensure_ascii=False,
        )
        errors = json.dumps(
            validation_error.errors(include_url=False),
            ensure_ascii=False,
        )
        return (
            "이전 응답이 JSON 형식 또는 출력 스키마 검증에 실패했습니다.\n"
            f"검증 오류: {errors}\n"
            f"반드시 다음 JSON Schema를 만족하는 JSON만 다시 반환하세요: {schema}\n"
            "설명, 사과, 마크다운 코드블록은 포함하지 마세요."
        )

    @staticmethod
    def _strip_code_fence(response_text: str) -> str:
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]).strip()
        return text
