import sys
import unittest
from pathlib import Path

import fitz
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.api.routers.meta_router import get_analysis_service
from app.main import app
from app.schemas.interview import MajorType, PreInterviewAnalysisResult


def build_sample_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Sample Project Portfolio\n"
        "Project: Interview Platform\n"
        "Role: Backend Developer\n"
        "Tech Stack: Python, FastAPI, PostgreSQL",
    )
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def build_analysis_result() -> PreInterviewAnalysisResult:
    questions = [
        {
            "question_id": f"Q{index}",
            "body": f"테스트 질문 {index}",
            "intent": "지원자의 기술적 판단을 확인합니다.",
            "source_project": "Interview Platform",
        }
        for index in range(1, 16)
    ]
    return PreInterviewAnalysisResult.model_validate(
        {
            "portfolio": {
                "projects": [
                    {
                        "name": "Interview Platform",
                        "summary": "IT 모의면접 플랫폼",
                        "role": "Backend Developer",
                        "tech_stack": ["Python", "FastAPI"],
                        "contributions": ["분석 API 구현"],
                        "achievements": [],
                        "challenges": [],
                    }
                ],
                "overall_tech_stack": ["Python", "FastAPI"],
                "primary_role": "Backend Developer",
                "career_summary": "백엔드 중심 프로젝트 경험이 있습니다.",
            },
            "github_repository": {
                "repo_name": "sample-repository",
                "repo_url": "https://github.com/example/sample-repository",
                "description": "테스트 저장소",
                "default_branch": "main",
                "language": "Python",
                "readme": "",
                "stacks": ["FastAPI"],
                "files": [],
            },
            "candidate_profile": {
                "candidate_summary": "백엔드 지원자",
                "primary_role": "Backend Developer",
                "experience_level": "Junior",
                "core_tech_stack": ["Python", "FastAPI"],
                "technical_strengths": ["API 구현"],
                "collaboration_strengths": [],
                "risk_factors": [],
                "project_highlights": [],
                "recommended_question_focus": ["API 설계"],
            },
            "original_questions": questions,
        }
    )


class FakeAnalysisService:
    def __init__(self):
        self.calls = []

    async def analyze(
        self,
        pdf_bytes: bytes,
        github_url: str,
        major: MajorType,
    ) -> PreInterviewAnalysisResult:
        self.calls.append(
            {
                "pdf_bytes": pdf_bytes,
                "github_url": github_url,
                "major": major,
            }
        )
        return build_analysis_result()


class AnalyzeInputTest(unittest.TestCase):
    def setUp(self):
        self.analysis_service = FakeAnalysisService()
        app.dependency_overrides[get_analysis_service] = lambda: self.analysis_service
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_accepts_portfolio_github_url_and_major(self):
        pdf_bytes = build_sample_pdf()

        response = self.client.post(
            "/portfolio/analyze",
            files={"portfolio": ("portfolio.pdf", pdf_bytes, "application/pdf")},
            data={
                "github_url": "https://github.com/example/sample-repository",
                "major": "backend",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(len(payload["data"]["original_questions"]), 15)
        self.assertEqual(len(self.analysis_service.calls), 1)
        self.assertEqual(self.analysis_service.calls[0]["pdf_bytes"], pdf_bytes)
        self.assertEqual(
            self.analysis_service.calls[0]["github_url"],
            "https://github.com/example/sample-repository",
        )
        self.assertEqual(self.analysis_service.calls[0]["major"], MajorType.BACKEND)

    def test_rejects_invalid_major(self):
        response = self.client.post(
            "/portfolio/analyze",
            files={"portfolio": ("portfolio.pdf", build_sample_pdf(), "application/pdf")},
            data={
                "github_url": "https://github.com/example/sample-repository",
                "major": "fullstack",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.analysis_service.calls, [])

    def test_rejects_missing_portfolio(self):
        response = self.client.post(
            "/portfolio/analyze",
            data={
                "github_url": "https://github.com/example/sample-repository",
                "major": "frontend",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.analysis_service.calls, [])


if __name__ == "__main__":
    unittest.main()
