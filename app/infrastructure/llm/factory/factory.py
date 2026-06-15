from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.client.claude.claude_client import ClaudeClient
from app.infrastructure.llm.client.openai.openai_client import OpenAIClient
from app.infrastructure.llm.dto.LLMModel import LLMModel


class LLMFactory:
    _instances: dict[LLMModel, BaseLLMClient] = {}

    @classmethod
    def get_client(cls, model: LLMModel) -> BaseLLMClient:
        if model not in cls._instances:
            if model == LLMModel.GPT:
                cls._instances[model] = OpenAIClient()
            elif model == LLMModel.CLAUDE:
                cls._instances[model] = ClaudeClient()
            else:
                raise ValueError(f"Unknown model: {model}")
        return cls._instances[model]
