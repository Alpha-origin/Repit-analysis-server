import logging
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core import CommonResponse
from schemas.interview import AnalysisAcceptedResponse, MajorType
from services.github_service import GithubService, GithubServiceError

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
logger = logging.getLogger(__name__)


# TODO(handoff): 이 엔드포인트는 최종적으로 "분석 작업 접수 API" 역할을 해야 한다.
# 현재는 analysis_request_id 만 반환하는 ack 형태까지만 반영되어 있다.
# 다음 단계에서 해야 할 일:
# 1. 업로드 파일 bytes 확보
# 2. background task 로 AnalysisJobService 실행 연결
# 3. github_url / major 검증 후 즉시 ack 반환
# 4. 분석 결과는 여기서 반환하지 않고 callback 으로 API 서버에 전달
@router.post("/analyze", response_model=CommonResponse[AnalysisAcceptedResponse])
async def analyze_metadata(
    portfolio: UploadFile = File(...),
    github_url: str = Form(...),
    major: MajorType = Form(...),
):
    analysis_request_id = str(uuid4())
    github_service = GithubService()

    try:
        github_service.extract_repo_info(github_url)
    except GithubServiceError as exc:
        logger.warning(
            "analysis request rejected request_id=%s github_url=%s reason=%s",
            analysis_request_id,
            github_url,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        await github_service.close()

    logger.info(
        "analysis request accepted request_id=%s major=%s github_url=%s",
        analysis_request_id,
        major.value,
        github_url,
    )

    return CommonResponse(
        message="analysis accepted",
        data=AnalysisAcceptedResponse(
            analysis_request_id=analysis_request_id,
        ),
    )
