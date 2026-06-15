from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core import CommonResponse
from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.dto.LLMModel import LLMModel
from app.infrastructure.llm.factory.factory import LLMFactory
from app.schemas.interview import MajorType, PreInterviewAnalysisResult
from app.services.github_service import GithubService, GithubServiceError
from app.services.interview_analysis_service import InterviewAnalysisService
from app.services.portfolio.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_llm_client() -> BaseLLMClient:
    return LLMFactory.get_client(LLMModel.CLAUDE)


def get_analysis_service(
    llm_client: BaseLLMClient = Depends(get_llm_client),
) -> InterviewAnalysisService:
    return InterviewAnalysisService(
        portfolio_service=PortfolioService(llm_client),
        github_service=GithubService(),
        llm_client=llm_client,
    )


@router.post("/analyze", response_model=CommonResponse[PreInterviewAnalysisResult])
async def analyze_metadata(
    portfolio: UploadFile = File(...),
    github_url: str = Form(...),
    major: MajorType = Form(...),
    analysis_service: InterviewAnalysisService = Depends(get_analysis_service),
):
    pdf_bytes = await portfolio.read()
    try:
        result = await analysis_service.analyze(
            pdf_bytes=pdf_bytes,
            github_url=github_url,
            major=major,
        )
    except GithubServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return CommonResponse(data=result)
