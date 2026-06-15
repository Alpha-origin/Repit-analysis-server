from infrastructure.llm.prompts.interview_prompt import (
    FEEDBACK_GENERATION_SYSTEM,
    build_feedback_generation_prompt,
)
from schemas.interview import InterviewFeedbackRequest, InterviewFeedbackResult
from services.structured_llm_service import StructuredLLMService


class InterviewFeedbackService(StructuredLLMService):
    async def generate_feedback(
        self,
        request_data: InterviewFeedbackRequest,
    ) -> InterviewFeedbackResult:
        messages = build_feedback_generation_prompt(request_data.model_dump())
        return await self.generate_structured_output(
            response_model=InterviewFeedbackResult,
            messages=messages,
            system_prompt=FEEDBACK_GENERATION_SYSTEM,
        )
