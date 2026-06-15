from pydantic import BaseModel, Field

from app.infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from app.infrastructure.llm.prompts.interview_prompt import (
    COMPREHENSIVE_PROFILE_SYSTEM,
    QUESTION_GENERATION_SYSTEM,
    build_comprehensive_profile_prompt,
    build_question_generation_prompt,
)
from app.schemas.interview import (
    CandidateComprehensiveProfile,
    MajorType,
    OriginalInterviewQuestion,
    PreInterviewAnalysisResult,
)
from app.services.github_service import GithubService
from app.services.portfolio.portfolio_service import PortfolioService
from app.services.structured_llm_service import StructuredLLMService

PRE_GENERATED_QUESTION_COUNT = 15


class QuestionGenerationResponse(BaseModel):
    original_questions: list[OriginalInterviewQuestion] = Field(min_length=15, max_length=15)


class InterviewAnalysisService(StructuredLLMService):
    def __init__(
        self,
        portfolio_service: PortfolioService,
        github_service: GithubService,
        llm_client: BaseLLMClient,
    ):
        super().__init__(llm_client)
        self._portfolio_service = portfolio_service
        self._github_service = github_service

    async def analyze(
        self,
        pdf_bytes: bytes,
        github_url: str,
        major: MajorType,
    ) -> PreInterviewAnalysisResult:
        portfolio_result = await self._portfolio_service.analyze(pdf_bytes)
        github_result = await self._github_service.analyze_repository(github_url)

        candidate_profile = await self._build_candidate_profile(
            portfolio_result.model_dump(),
            github_result,
            major,
        )
        questions = await self._build_original_questions(
            candidate_profile,
            major,
            PRE_GENERATED_QUESTION_COUNT,
        )

        return PreInterviewAnalysisResult(
            portfolio=portfolio_result,
            github_repository=github_result,
            candidate_profile=candidate_profile,
            original_questions=questions,
        )

    async def _build_candidate_profile(
        self,
        portfolio_data: dict,
        github_data: dict,
        major: MajorType,
    ) -> CandidateComprehensiveProfile:
        messages = build_comprehensive_profile_prompt(portfolio_data, github_data, major)
        return await self.generate_structured_output(
            response_model=CandidateComprehensiveProfile,
            messages=messages,
            system_prompt=COMPREHENSIVE_PROFILE_SYSTEM,
        )

    async def _build_original_questions(
        self,
        candidate_profile: CandidateComprehensiveProfile,
        major: MajorType,
        question_count: int,
    ) -> list[OriginalInterviewQuestion]:
        messages = build_question_generation_prompt(
            candidate_profile.model_dump(),
            major,
            question_count,
        )
        result = await self.generate_structured_output(
            response_model=QuestionGenerationResponse,
            messages=messages,
            system_prompt=QUESTION_GENERATION_SYSTEM,
        )
        return result.original_questions
