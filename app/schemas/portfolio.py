from typing import Optional

from pydantic import BaseModel, Field


class ProjectSchema(BaseModel):
    """포트폴리오 내 개별 프로젝트"""
    name: str = Field(description="프로젝트 이름")
    summary: str = Field(description="프로젝트 한 줄 요약")
    role: str = Field(description="본인 역할 (예: 백엔드 개발, 팀장, 프론트엔드 등)")
    tech_stack: list[str] = Field(default_factory=list, description="사용 기술 스택 목록")
    contributions: list[str] = Field(default_factory=list, description="본인의 주요 기여/구현 내용")
    achievements: list[str] = Field(default_factory=list, description="정량적·정성적 성과 (예: 응답속도 30% 개선)")
    challenges: list[str] = Field(default_factory=list, description="겪은 기술적 도전 과제 및 해결 방법")
    team_size: Optional[int] = Field(default=None, description="팀 인원 수 (파악 가능할 경우)")
    duration: Optional[str] = Field(default=None, description="프로젝트 기간 (예: 2024.03 ~ 2024.06)")


class PortfolioAnalysisResult(BaseModel):
    """PDF 포트폴리오 전체 분석 결과"""
    projects: list[ProjectSchema] = Field(default_factory=list, description="추출된 프로젝트 목록")
    overall_tech_stack: list[str] = Field(default_factory=list, description="전체 포트폴리오 통합 기술 스택")
    primary_role: str = Field(description="지원자의 주요 포지션 (예: 백엔드 개발자, 풀스택 개발자)")
    career_summary: str = Field(description="포트폴리오 전반에 대한 종합 요약 (2~3문장)")


class GithubRepositoryFile(BaseModel):
    name: str = Field(description="파일 이름")
    path: str = Field(description="저장소 내 파일 경로")
    extension: str = Field(default="", description="파일 확장자")
    download_url: Optional[str] = Field(default=None, description="원본 파일 다운로드 URL")
    size: Optional[int] = Field(default=None, description="파일 크기(bytes)")


class GithubRepositoryAnalysisResult(BaseModel):
    repo_name: str = Field(description="저장소 이름")
    repo_url: Optional[str] = Field(default=None, description="저장소 URL")
    description: str = Field(default="", description="저장소 설명")
    default_branch: str = Field(default="", description="기본 브랜치")
    language: Optional[str] = Field(default=None, description="대표 언어")
    readme: str = Field(default="", description="README 내용")
    stacks: list[str] = Field(default_factory=list, description="추론된 기술 스택")
    files: list[GithubRepositoryFile] = Field(default_factory=list, description="분석 대상 파일 목록")
