from fastapi import APIRouter, UploadFile, File, Form, Depends
from core import CommonResponse
from services import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_portfolio_service():
    return PortfolioService()


@router.post("/analyze", response_model=CommonResponse)
async def analyze_portfolio(
    portfolio: UploadFile = File(...),
    github_url: str = Form(...),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    pdf_bytes = await portfolio.read()
    portfolio_text = await portfolio_service.get_portfolio_text(pdf_bytes)

    # TODO: LLM 호출로 포트폴리오 데이터 구조화 (다음 단계)
    return CommonResponse(data={"portfolio_text": portfolio_text})
