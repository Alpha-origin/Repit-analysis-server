from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from core import CommonResponse
from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.dto.LLMModel import LLMModel
from infrastructure.llm.factory.factory import LLMFactory
from schemas.interview import (
    InterviewFeedbackRequest,
    InterviewFeedbackResult,
    InterviewGenerationOptions,
    InterviewPipelineResult,
)
from services.github_service import GithubService
from services.github_service import GithubServiceError
from services.interview_feedback_service import InterviewFeedbackService
from services.interview_pipeline_service import InterviewPipelineService
from services.portfolio.portfolio_service import PortfolioService

router = APIRouter(prefix="/interview", tags=["interview"])


def get_llm_client() -> BaseLLMClient:
    return LLMFactory.get_client(LLMModel.CLAUDE)


def get_pipeline_service(
    llm_client: BaseLLMClient = Depends(get_llm_client),
) -> InterviewPipelineService:
    portfolio_service = PortfolioService(llm_client)
    github_service = GithubService()
    return InterviewPipelineService(portfolio_service, github_service, llm_client)


def get_feedback_service(
    llm_client: BaseLLMClient = Depends(get_llm_client),
) -> InterviewFeedbackService:
    return InterviewFeedbackService(llm_client)


def _parse_focus_topics(raw_focus_topics: str) -> list[str]:
    return [topic.strip() for topic in raw_focus_topics.split(",") if topic.strip()]


@router.post("/pipeline", response_model=CommonResponse[InterviewPipelineResult])
async def build_interview_pipeline(
    portfolio: UploadFile = File(...),
    github_url: str = Form(...),
    interview_atmosphere: str = Form(...),
    interviewer_style: str = Form(...),
    difficulty: str = Form(...),
    focus_topics: str = Form(default=""),
    question_count: int = Form(default=5),
    pipeline_service: InterviewPipelineService = Depends(get_pipeline_service),
):
    pdf_bytes = await portfolio.read()
    options = InterviewGenerationOptions(
        interview_atmosphere=interview_atmosphere,
        interviewer_style=interviewer_style,
        difficulty=difficulty,
        focus_topics=_parse_focus_topics(focus_topics),
        question_count=question_count,
    )
    try:
        result = await pipeline_service.build_pipeline(pdf_bytes, github_url, options)
    except GithubServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return CommonResponse(data=result)


@router.post("/feedback", response_model=CommonResponse[InterviewFeedbackResult])
async def generate_interview_feedback(
    request_data: InterviewFeedbackRequest,
    feedback_service: InterviewFeedbackService = Depends(get_feedback_service),
):
    result = await feedback_service.generate_feedback(request_data)
    return CommonResponse(data=result)
