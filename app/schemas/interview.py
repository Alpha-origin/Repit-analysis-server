from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from schemas.portfolio import GithubRepositoryAnalysisResult, PortfolioAnalysisResult


class MajorType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"


class InterviewSettings(BaseModel):
    interview_atmosphere: str = Field(description="면접 분위기")
    interviewer_style: str = Field(description="면접관 스타일")
    difficulty: str = Field(description="면접 난이도")
    focus_topics: list[str] = Field(default_factory=list, description="집중적으로 다루고 싶은 주제")


class CandidateProjectHighlight(BaseModel):
    name: str = Field(description="질문 후보가 되는 프로젝트 이름")
    role: str = Field(description="해당 프로젝트에서 지원자의 역할")
    summary: str = Field(description="프로젝트 핵심 요약")
    relevance: str = Field(description="이 프로젝트를 질문 근거로 삼는 이유")
    evidence: list[str] = Field(default_factory=list, description="포트폴리오/깃허브에서 추출한 근거")
    tech_stack: list[str] = Field(default_factory=list, description="프로젝트 연관 기술 스택")


class CandidateComprehensiveProfile(BaseModel):
    candidate_summary: str = Field(description="지원자 종합 요약")
    primary_role: str = Field(description="판단된 주요 포지션")
    experience_level: str = Field(description="주니어/미드레벨 등 추정 레벨")
    core_tech_stack: list[str] = Field(default_factory=list, description="핵심 기술 스택")
    technical_strengths: list[str] = Field(default_factory=list, description="기술 강점")
    collaboration_strengths: list[str] = Field(default_factory=list, description="협업 강점")
    risk_factors: list[str] = Field(default_factory=list, description="면접에서 검증이 필요한 약점/리스크")
    project_highlights: list[CandidateProjectHighlight] = Field(default_factory=list, description="질문 근거 프로젝트")
    recommended_question_focus: list[str] = Field(default_factory=list, description="면접에서 우선 검증할 주제")


class OriginalInterviewQuestion(BaseModel):
    question_id: str = Field(description="원질문 식별자")
    body: str = Field(description="원질문 본문")
    intent: str = Field(description="질문 의도")
    source_project: Optional[str] = Field(default=None, description="질문 근거 프로젝트")
    category: Optional[str] = Field(default=None, description="질문 카테고리")
    key_keywords: list[str] = Field(default_factory=list, description="핵심 키워드")
    evaluation_points: list[str] = Field(default_factory=list, description="답변 평가 포인트")
    difficulty: Optional[str] = Field(default=None, description="질문 난이도")


class PreInterviewAnalysisResult(BaseModel):
    portfolio: PortfolioAnalysisResult = Field(description="포트폴리오 분석 결과")
    github_repository: GithubRepositoryAnalysisResult = Field(description="깃허브 분석 결과")
    candidate_profile: CandidateComprehensiveProfile = Field(description="종합 지원자 프로필")
    original_questions: list[OriginalInterviewQuestion] = Field(
        min_length=15,
        max_length=15,
        description="생성된 원질문 15개",
    )


class AnsweredInterviewQuestion(BaseModel):
    question_id: str = Field(description="질문 식별자")
    body: str = Field(description="질문 본문")
    intent: str = Field(description="질문 의도")
    key_keywords: list[str] = Field(default_factory=list, description="질문 핵심 키워드")
    source_project: Optional[str] = Field(default=None, description="질문 근거 프로젝트")
    candidate_answer: str = Field(description="지원자 답변")
    tail_questions: list[str] = Field(default_factory=list, description="실제 진행된 꼬리질문")
    interviewer_notes: Optional[str] = Field(default=None, description="면접 진행 메모")


class InterviewScorecard(BaseModel):
    technical_depth: int = Field(ge=1, le=5, description="기술 깊이 점수")
    problem_solving: int = Field(ge=1, le=5, description="문제 해결 점수")
    communication: int = Field(ge=1, le=5, description="커뮤니케이션 점수")
    collaboration: int = Field(ge=1, le=5, description="협업 역량 점수")
    growth_potential: int = Field(ge=1, le=5, description="성장 가능성 점수")


class OverallInterviewFeedback(BaseModel):
    summary: str = Field(description="면접 전체 총평")
    hiring_signal: str = Field(description="채용 시그널 요약")
    strengths: list[str] = Field(default_factory=list, description="전반 강점")
    weaknesses: list[str] = Field(default_factory=list, description="전반 보완점")
    recommendations: list[str] = Field(default_factory=list, description="향후 개선 제안")
    scorecard: InterviewScorecard = Field(description="종합 평가 점수표")


class QuestionFeedback(BaseModel):
    question_id: str = Field(description="질문 식별자")
    verdict: str = Field(description="질문 단위 평가")
    answer_summary: str = Field(description="답변 요약")
    strengths: list[str] = Field(default_factory=list, description="잘한 점")
    improvements: list[str] = Field(default_factory=list, description="개선 포인트")
    missed_keywords: list[str] = Field(default_factory=list, description="놓친 핵심 키워드")
    follow_up_needed: bool = Field(description="추가 검증 필요 여부")


class InterviewFeedbackRequest(BaseModel):
    interview_settings: InterviewSettings = Field(description="면접 설정")
    candidate_profile: CandidateComprehensiveProfile = Field(description="사전 생성된 종합 프로필")
    questions: list[AnsweredInterviewQuestion] = Field(default_factory=list, description="질문/답변 목록")
    portfolio: Optional[PortfolioAnalysisResult] = Field(default=None, description="선택적 포트폴리오 분석 결과")
    github_repository: Optional[GithubRepositoryAnalysisResult] = Field(default=None, description="선택적 깃허브 분석 결과")


class InterviewFeedbackResult(BaseModel):
    overall_feedback: OverallInterviewFeedback = Field(description="면접 전체 피드백")
    question_feedback: list[QuestionFeedback] = Field(default_factory=list, description="질문별 피드백")
