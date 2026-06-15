import logging

from schemas.interview import MajorType
from services.analysis_callback_service import AnalysisCallbackService
from services.interview_pipeline_service import (
    PRE_GENERATED_QUESTION_COUNT,
    InterviewPipelineService,
)

logger = logging.getLogger(__name__)


class AnalysisJobService:
    # TODO(handoff): 이 클래스는 비동기 분석 작업의 실행기 초안이다.
    # 아직 어떤 라우터에서도 호출되지 않는다.
    # 다음 단계에서는 /portfolio/analyze 접수 후 background task 에서
    # process_analysis_request(...) 를 실행하도록 연결해야 한다.
    def __init__(
        self,
        pipeline_service: InterviewPipelineService,
        callback_service: AnalysisCallbackService,
    ):
        self._pipeline_service = pipeline_service
        self._callback_service = callback_service

    async def process_analysis_request(
        self,
        analysis_request_id: str,
        pdf_bytes: bytes,
        github_url: str,
        major: MajorType,
    ) -> None:
        # TODO(handoff): 실패 시 현재는 로그만 남긴다.
        # 추후 필요하면 상태 저장, 재처리 정책, dead-letter 성격의 후속 처리도 고려할 수 있다.
        logger.info("analysis job started request_id=%s", analysis_request_id)
        try:
            result = await self._pipeline_service.build_pre_interview_result(
                pdf_bytes=pdf_bytes,
                github_url=github_url,
                major=major,
                question_count=PRE_GENERATED_QUESTION_COUNT,
            )
            await self._callback_service.send_analysis_result(analysis_request_id, result)
            logger.info("analysis job finished request_id=%s", analysis_request_id)
        except Exception:
            logger.exception("analysis job failed request_id=%s", analysis_request_id)
