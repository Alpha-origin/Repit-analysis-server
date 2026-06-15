import json
import sys
import unittest
from pathlib import Path

from pydantic import BaseModel, Field

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.response import LLMResponse
from services.structured_llm_service import StructuredLLMService


class FifteenItemsResponse(BaseModel):
    items: list[int] = Field(min_length=15, max_length=15)


class FakeLLMClient(BaseLLMClient):
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)
        self.requests = []

    async def generate(self, request):
        self.requests.append(request)
        return LLMResponse(
            response_text=next(self._responses),
            stop_reason="end_turn",
            input_tokens=1,
            output_tokens=1,
        )


class StructuredLLMServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_retries_invalid_json_and_returns_valid_result(self):
        client = FakeLLMClient(
            [
                "not-json",
                json.dumps({"items": list(range(15))}),
            ]
        )
        service = StructuredLLMService(client)

        result = await service.generate_structured_output(
            response_model=FifteenItemsResponse,
            messages=[{"role": "user", "content": "generate"}],
            system_prompt="return json",
        )

        self.assertEqual(result.items, list(range(15)))
        self.assertEqual(len(client.requests), 2)
        self.assertIn("검증에 실패", client.requests[1].message[-1]["content"])

    async def test_retries_when_item_count_is_not_fifteen(self):
        client = FakeLLMClient(
            [
                json.dumps({"items": list(range(14))}),
                json.dumps({"items": list(range(15))}),
            ]
        )
        service = StructuredLLMService(client)

        result = await service.generate_structured_output(
            response_model=FifteenItemsResponse,
            messages=[{"role": "user", "content": "generate"}],
            system_prompt="return json",
        )

        self.assertEqual(len(result.items), 15)
        self.assertEqual(len(client.requests), 2)

    async def test_raises_after_three_invalid_responses(self):
        client = FakeLLMClient(["{}", "{}", "{}"])
        service = StructuredLLMService(client)

        with self.assertRaisesRegex(ValueError, "총 3회 시도"):
            await service.generate_structured_output(
                response_model=FifteenItemsResponse,
                messages=[{"role": "user", "content": "generate"}],
                system_prompt="return json",
            )

        self.assertEqual(len(client.requests), 3)


if __name__ == "__main__":
    unittest.main()
