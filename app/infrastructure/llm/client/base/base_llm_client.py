from abc import abstractmethod, ABC

from app.infrastructure.llm.dto.request import LLMRequest
from app.infrastructure.llm.dto.response import LLMResponse


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(
            self,
            request: LLMRequest
    ) -> LLMResponse:
        pass