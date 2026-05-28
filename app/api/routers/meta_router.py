from fastapi import APIRouter, UploadFile, File, Form, Depends
from core import CommonResponse
from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.LLMModel import LLMModel
from infrastructure.llm.factory.factory import LLMFactory
from schemas.portfolio import PortfolioAnalysisResult
from services import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_llm_client() -> BaseLLMClient:
    return LLMFactory.get_client(LLMModel.CLAUDE)


def get_portfolio_service(llm_client: BaseLLMClient = Depends(get_llm_client)) -> PortfolioService:
    return PortfolioService(llm_client)


@router.post("/analyze", response_model=CommonResponse[PortfolioAnalysisResult])
async def analyze_metadata(
    portfolio: UploadFile = File(...),
    github_url: str = Form(...),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    pdf_bytes = await portfolio.read()
    result = await portfolio_service.analyze(pdf_bytes)

    # TODO: github_url 분석 연동 (다음 단계)
    return CommonResponse(data=result)
