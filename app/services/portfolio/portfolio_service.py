import json

from pydantic import ValidationError

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.request import LLMRequest
from infrastructure.llm.prompts.portfolio_prompt import (
    PORTFOLIO_ANALYSIS_SYSTEM,
    build_portfolio_analysis_prompt,
)
from schemas.portfolio import PortfolioAnalysisResult
from services.portfolio.pdf_parse.pdf_parser import PdfParser


class PortfolioService:

    def __init__(self, llm_client: BaseLLMClient):
        self._pdf_parser = PdfParser()
        self._llm_client = llm_client

    async def analyze(self, pdf_bytes: bytes) -> PortfolioAnalysisResult:
        """PDF bytes → 포트폴리오 구조화 결과 반환"""
        portfolio_text = self._pdf_parser.parse(pdf_bytes)
        return await self._analyze_with_llm(portfolio_text)

    async def get_portfolio_text(self, pdf_bytes: bytes) -> str:
        """PDF bytes → 정제된 텍스트만 반환 (디버그용)"""
        return self._pdf_parser.parse(pdf_bytes)

    async def _analyze_with_llm(self, portfolio_text: str) -> PortfolioAnalysisResult:
        messages = build_portfolio_analysis_prompt(portfolio_text)

        request = LLMRequest(
            message=messages,
            system=PORTFOLIO_ANALYSIS_SYSTEM,
            temperature=0.2,
            max_tokens=4096,
        )

        response = await self._llm_client.generate(request)
        return self._parse_llm_response(response.response_text)

    def _parse_llm_response(self, response_text: str) -> PortfolioAnalysisResult:
        """LLM 응답 텍스트를 PortfolioAnalysisResult로 파싱"""
        # 혹시 마크다운 코드블록이 포함된 경우 제거
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM이 유효하지 않은 JSON을 반환했습니다: {e}") from e

        try:
            return PortfolioAnalysisResult(**data)
        except ValidationError as e:
            raise ValueError(f"LLM 응답이 예상 스키마와 다릅니다: {e}") from e
