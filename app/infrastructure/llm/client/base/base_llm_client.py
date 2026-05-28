from abc import abstractmethod, ABC

from infrastructure.llm.dto.request import LLMRequest
from infrastructure.llm.dto.response import LLMResponse


class BaseLLMClient(ABC):
    @abstractmethod
    async def generate(
            self,
            request: LLMRequest
    ) -> LLMResponse:
        pass