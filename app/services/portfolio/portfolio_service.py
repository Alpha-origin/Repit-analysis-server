from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.prompts.portfolio_prompt import (
    PORTFOLIO_ANALYSIS_SYSTEM,
    build_portfolio_analysis_prompt,
)
from app.schemas.portfolio import PortfolioAnalysisResult
from app.services.portfolio.pdf_parse.pdf_parser import PdfParser
from app.services.structured_llm_service import StructuredLLMService


class PortfolioService(StructuredLLMService):

    def __init__(self, llm_client: BaseLLMClient):
        super().__init__(llm_client)
        self._pdf_parser = PdfParser()

    async def analyze(self, pdf_bytes: bytes) -> PortfolioAnalysisResult:
        """PDF bytes → 포트폴리오 구조화 결과 반환"""
        portfolio_text = self._pdf_parser.parse(pdf_bytes)
        return await self._analyze_with_llm(portfolio_text)

    async def get_portfolio_text(self, pdf_bytes: bytes) -> str:
        """PDF bytes → 정제된 텍스트만 반환 (디버그용)"""
        return self._pdf_parser.parse(pdf_bytes)

    async def _analyze_with_llm(self, portfolio_text: str) -> PortfolioAnalysisResult:
        messages = build_portfolio_analysis_prompt(portfolio_text)
        return await self.generate_structured_output(
            response_model=PortfolioAnalysisResult,
            messages=messages,
            system_prompt=PORTFOLIO_ANALYSIS_SYSTEM,
        )
