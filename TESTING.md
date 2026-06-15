# Input Test

## Automated Input Contract Test

LLM과 GitHub API를 호출하지 않고 `/portfolio/analyze`의 multipart 입력 계약을 검증한다.

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

검증 항목:

- PDF, GitHub URL, major 입력 수신
- `major=frontend|backend` enum 검증
- 포트폴리오 누락 시 422 응답
- 응답에 원질문 15개 포함

## Analyze Smoke Test

먼저 서버를 실행한다.

```bash
./.venv/bin/python -m uvicorn app.main:app --reload
```

다른 터미널에서 실제 PDF와 공개 GitHub 저장소로 호출한다.

```bash
./.venv/bin/python scripts/smoke_analyze.py \
  /absolute/path/to/portfolio.pdf \
  https://github.com/owner/repository \
  --major backend
```

스크립트는 HTTP 상태, 전체 처리 시간, JSON 응답을 출력하고 원질문이 정확히 15개인지 확인한다.
