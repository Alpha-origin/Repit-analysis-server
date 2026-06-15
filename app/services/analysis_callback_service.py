import asyncio
import hashlib
import hmac
import json
import logging
from urllib.parse import urljoin

import httpx

from core.config import settings
from schemas.interview import AnalysisCallbackPayload, PreInterviewAnalysisResult

logger = logging.getLogger(__name__)


class AnalysisCallbackService:
    # TODO(handoff): 이 서비스는 callback 전송 초안이다.
    # 구현 연결 전 확인할 것:
    # 1. config 에 callback 관련 env 추가
    # 2. API 서버와 header / payload 계약 확정
    # 3. 실제 라우터 -> AnalysisJobService -> 이 서비스까지 호출 흐름 연결
    SIGNATURE_HEADER = "X-Analysis-Signature"
    REQUEST_ID_HEADER = "X-Analysis-Request-Id"

    def __init__(self, max_retries: int = 3, timeout: float = 15.0):
        self._max_retries = max_retries
        self._timeout = timeout

    async def send_analysis_result(
        self,
        analysis_request_id: str,
        result: PreInterviewAnalysisResult,
    ) -> None:
        # TODO(handoff): payload 는 analysis_request_id + portfolio + github_repository
        # + candidate_profile + original_questions 를 한 번에 보내는 형태로 가정한다.
        payload = AnalysisCallbackPayload(
            analysis_request_id=analysis_request_id,
            **result.model_dump(),
        )
        body = json.dumps(
            payload.model_dump(mode="json"),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        callback_url = self._build_callback_url()
        headers = {
            "Content-Type": "application/json",
            self.REQUEST_ID_HEADER: analysis_request_id,
            self.SIGNATURE_HEADER: self._build_signature(body),
        }

        for attempt in range(1, self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        callback_url,
                        content=body,
                        headers=headers,
                    )
                    response.raise_for_status()
                logger.info(
                    "analysis callback delivered request_id=%s attempt=%s",
                    analysis_request_id,
                    attempt,
                )
                return
            except httpx.HTTPError as exc:
                logger.warning(
                    "analysis callback failed request_id=%s attempt=%s error=%s",
                    analysis_request_id,
                    attempt,
                    exc,
                )
                if attempt == self._max_retries:
                    raise
                await asyncio.sleep(attempt)

    def _build_callback_url(self) -> str:
        # TODO(handoff): 현재 설정값 누락 시 ValueError 를 던진다.
        # 실제 연결 전에 Settings 에 env 필드 추가가 필요하다.
        if not settings.API_SERVER_BASE_URL or not settings.ANALYSIS_CALLBACK_PATH:
            raise ValueError("API_SERVER_BASE_URL 또는 ANALYSIS_CALLBACK_PATH 설정이 누락되었습니다.")
        return urljoin(
            f"{settings.API_SERVER_BASE_URL.rstrip('/')}/",
            settings.ANALYSIS_CALLBACK_PATH.lstrip("/"),
        )

    def _build_signature(self, body: bytes) -> str:
        if not settings.ANALYSIS_CALLBACK_SECRET:
            raise ValueError("ANALYSIS_CALLBACK_SECRET 설정이 누락되었습니다.")
        digest = hmac.new(
            settings.ANALYSIS_CALLBACK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"
