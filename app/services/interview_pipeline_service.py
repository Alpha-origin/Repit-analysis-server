from pydantic import BaseModel, Field

from infrastructure.llm.client.base.base_llm_client import BaseLLMClient
from infrastructure.llm.prompts.interview_prompt import (
    COMPREHENSIVE_PROFILE_SYSTEM,
    QUESTION_GENERATION_SYSTEM,
    build_comprehensive_profile_prompt,
    build_question_generation_prompt,
)
from schemas.interview import (
    CandidateComprehensiveProfile,
    InterviewGenerationOptions,
    InterviewPipelineResult,
    MajorType,
    OriginalInterviewQuestion,
    PreInterviewAnalysisResult,
)
from services.github_service import GithubService
from services.portfolio.portfolio_service import PortfolioService
from services.structured_llm_service import StructuredLLMService

PRE_GENERATED_QUESTION_COUNT = 15


class QuestionGenerationResponse(BaseModel):
    original_questions: list[OriginalInterviewQuestion] = Field(default_factory=list)


class InterviewPipelineService(StructuredLLMService):
    # TODO(handoff): 이 서비스는 현재 두 역할이 섞여 있다.
    # - 기존 /interview/pipeline 동기 호출용 build_pipeline
    # - 새 비동기 사전 분석 플로우용 build_pre_interview_result
    # 이후 세션에서는 운영 경로를 하나로 정리해야 한다.
    # 현재 우선순위는 build_pre_interview_result 를 /portfolio/analyze 의 background task 에 연결하는 것이다.
    def __init__(
        self,
        portfolio_service: PortfolioService,
        github_service: GithubService,
        llm_client: BaseLLMClient,
    ):
        super().__init__(llm_client)
        self._portfolio_service = portfolio_service
        self._github_service = github_service

    async def build_pipeline(
        self,
        pdf_bytes: bytes,
        github_url: str,
        options: InterviewGenerationOptions,
    ) -> InterviewPipelineResult:
        major = options.major or MajorType.BACKEND
        result = await self.build_pre_interview_result(
            pdf_bytes=pdf_bytes,
            github_url=github_url,
            major=major,
            question_count=options.question_count,
        )
        return InterviewPipelineResult(**result.model_dump())

    async def build_pre_interview_result(
        self,
        pdf_bytes: bytes,
        github_url: str,
        major: MajorType,
        question_count: int = PRE_GENERATED_QUESTION_COUNT,
    ) -> PreInterviewAnalysisResult:
        # TODO(handoff): 새 비동기 플로우의 핵심 오케스트레이션 메서드.
        # 기대 순서:
        # 1. portfolio 분석
        # 2. github 분석
        # 3. candidate_profile 생성
        # 4. original_questions 15개 생성
        # 5. 결과를 callback payload 로 전달
        portfolio_result = await self._portfolio_service.analyze(pdf_bytes)
        github_result = await self._github_service.analyze_repository(github_url)

        candidate_profile = await self._build_candidate_profile(
            portfolio_result.model_dump(),
            github_result,
            major,
        )
        questions = await self._build_original_questions(candidate_profile, major, question_count)

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
