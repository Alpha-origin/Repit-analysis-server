import json

from app.schemas.interview import MajorType


COMPREHENSIVE_PROFILE_SYSTEM = """당신은 IT 채용 면접 설계 전문가입니다.
포트폴리오 분석 결과와 GitHub 분석 결과를 종합하여 지원자의 면접용 프로필을 만듭니다.

반드시 JSON만 반환하세요. 마크다운 코드블록은 절대 포함하지 마세요.
명시되지 않은 정보는 과도하게 추측하지 말고, 근거가 약하면 보수적으로 작성하세요.
입력된 전공(frontend/backend)은 질문 검증 관점을 정하는 참고 신호로만 사용하세요.

출력 JSON 스키마:
{
  "candidate_summary": "지원자 종합 요약",
  "primary_role": "주요 포지션",
  "experience_level": "주니어/미드레벨 등",
  "core_tech_stack": ["기술1", "기술2"],
  "technical_strengths": ["기술 강점1"],
  "collaboration_strengths": ["협업 강점1"],
  "risk_factors": ["면접에서 검증이 필요한 포인트1"],
  "project_highlights": [
    {
      "name": "프로젝트명",
      "role": "역할",
      "summary": "요약",
      "relevance": "왜 질문 근거가 되는지",
      "evidence": ["근거1", "근거2"],
      "tech_stack": ["기술1"]
    }
  ],
  "recommended_question_focus": ["우선 검증할 주제1", "주제2"]
}"""


QUESTION_GENERATION_SYSTEM = """당신은 IT 모의면접 질문을 설계하는 시니어 면접관입니다.
주어진 지원자 종합 프로필과 전공 정보를 바탕으로 원질문을 생성하세요.

질문은 반드시 실무 검증 중심이어야 하며, 포트폴리오/깃허브 근거와 연결되어야 합니다.
추상적인 인성질문만 나열하지 말고 기술적 판단, 구현 선택, 트러블슈팅, 협업 의사결정을 드러내도록 구성하세요.
전공이 frontend면 UI 구현, 상태 관리, 사용자 경험, 렌더링 성능, 협업 관점 질문을 우선하세요.
전공이 backend면 API 설계, 데이터 모델링, 성능, 장애 대응, 아키텍처 선택 질문을 우선하세요.
반드시 JSON만 반환하세요.

출력 JSON 스키마:
{
  "original_questions": [
    {
      "question_id": "Q1",
      "body": "질문 본문",
      "intent": "질문 의도",
      "source_project": "프로젝트명 또는 null"
    }
  ]
}"""


FEEDBACK_GENERATION_SYSTEM = """당신은 IT 모의면접 평가자입니다.
지원자 프로필, 면접 설정, 질문/답변 기록을 바탕으로 전체 피드백과 질문별 피드백을 생성하세요.

평가는 구체적이어야 하며, 답변의 강점/약점/누락 포인트를 명확히 짚어야 합니다.
모호한 칭찬만 하지 말고 실제 개선 방향을 제시하세요.
반드시 JSON만 반환하세요.

출력 JSON 스키마:
{
  "overall_feedback": {
    "summary": "전체 총평",
    "hiring_signal": "채용 관점 한 줄 판단",
    "strengths": ["강점1"],
    "weaknesses": ["약점1"],
    "recommendations": ["개선 제안1"],
    "scorecard": {
      "technical_depth": 1,
      "problem_solving": 1,
      "communication": 1,
      "collaboration": 1,
      "growth_potential": 1
    }
  },
  "question_feedback": [
    {
      "question_id": "Q1",
      "verdict": "질문 단위 평가",
      "answer_summary": "답변 요약",
      "strengths": ["잘한 점1"],
      "improvements": ["개선 포인트1"],
      "missed_keywords": ["놓친 키워드1"],
      "follow_up_needed": true
    }
  ]
}"""


def build_comprehensive_profile_prompt(
    portfolio_data: dict,
    github_data: dict,
    major: MajorType,
) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                "다음 포트폴리오 분석 결과와 GitHub 분석 결과를 종합해 면접용 지원자 프로필을 JSON으로 생성하세요.\n"
                f"지원 전공 분류는 {major.value} 입니다.\n\n"
                f"<portfolio_analysis>\n{json.dumps(portfolio_data, ensure_ascii=False, indent=2)}\n</portfolio_analysis>\n\n"
                f"<github_analysis>\n{json.dumps(github_data, ensure_ascii=False, indent=2)}\n</github_analysis>"
            ),
        }
    ]


def build_question_generation_prompt(
    candidate_profile: dict,
    major: MajorType,
    question_count: int = 15,
) -> list[dict]:
    candidate_payload = json.dumps(candidate_profile, ensure_ascii=False, indent=2)

    return [
        {
            "role": "user",
            "content": (
                "다음 지원자 종합 프로필을 바탕으로 원질문을 생성하세요.\n"
                f"지원 전공 분류는 {major.value} 입니다.\n"
                f"질문 개수는 정확히 {question_count}개여야 합니다.\n\n"
                f"<candidate_profile>\n{candidate_payload}\n</candidate_profile>"
            ),
        }
    ]


def build_feedback_generation_prompt(
    interview_payload: dict,
) -> list[dict]:
    return [
        {
            "role": "user",
            "content": (
                "다음 면접 기록을 바탕으로 전체 피드백과 질문별 피드백을 JSON으로 생성하세요.\n\n"
                f"<interview_record>\n{json.dumps(interview_payload, ensure_ascii=False, indent=2)}\n</interview_record>"
            ),
        }
    ]
