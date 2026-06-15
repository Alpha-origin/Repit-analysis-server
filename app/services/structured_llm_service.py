import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.request import LLMRequest

T = TypeVar("T", bound=BaseModel)


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
    ) -> T:
        request = LLMRequest(
            message=messages,
            system=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        response = await self._llm_client.generate(request)
        text = self._strip_code_fence(response.response_text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM이 유효하지 않은 JSON을 반환했습니다: {exc}") from exc

        try:
            return response_model(**data)
        except ValidationError as exc:
            raise ValueError(f"LLM 응답이 예상 스키마와 다릅니다: {exc}") from exc

    @staticmethod
    def _strip_code_fence(response_text: str) -> str:
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]).strip()
        return text
