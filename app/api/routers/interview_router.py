from fastapi import APIRouter, Depends

from app.core import CommonResponse
from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.dto.LLMModel import LLMModel
from app.infrastructure.llm.factory.factory import LLMFactory
from app.schemas.interview import (
    InterviewFeedbackRequest,
    InterviewFeedbackResult,
)
from app.services.interview_feedback_service import InterviewFeedbackService

router = APIRouter(prefix="/interview", tags=["interview"])


def get_llm_client() -> BaseLLMClient:
    return LLMFactory.get_client(LLMModel.CLAUDE)


def get_feedback_service(
    llm_client: BaseLLMClient = Depends(get_llm_client),
) -> InterviewFeedbackService:
    return InterviewFeedbackService(llm_client)


@router.post("/feedback", response_model=CommonResponse[InterviewFeedbackResult])
async def generate_interview_feedback(
    request_data: InterviewFeedbackRequest,
    feedback_service: InterviewFeedbackService = Depends(get_feedback_service),
):
    result = await feedback_service.generate_feedback(request_data)
    return CommonResponse(data=result)
