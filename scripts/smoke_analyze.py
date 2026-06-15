import argparse
import json
import time
from pathlib import Path

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="실행 중인 분석 서버의 /portfolio/analyze API를 호출합니다.",
    )
    parser.add_argument("portfolio", type=Path, help="테스트할 포트폴리오 PDF 경로")
    parser.add_argument("github_url", help="분석할 공개 GitHub 저장소 URL")
    parser.add_argument(
        "--major",
        choices=("frontend", "backend"),
        default="backend",
        help="지원 전공 분류",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="실행 중인 분석 서버 주소",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="요청 제한 시간(초)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.portfolio.is_file():
        raise SystemExit(f"포트폴리오 파일을 찾을 수 없습니다: {args.portfolio}")
    if args.portfolio.suffix.lower() != ".pdf":
        raise SystemExit("포트폴리오 파일은 PDF여야 합니다.")

    endpoint = f"{args.base_url.rstrip('/')}/portfolio/analyze"
    started_at = time.perf_counter()

    with args.portfolio.open("rb") as portfolio_file:
        response = httpx.post(
            endpoint,
            files={
                "portfolio": (
                    args.portfolio.name,
                    portfolio_file,
                    "application/pdf",
                )
            },
            data={
                "github_url": args.github_url,
                "major": args.major,
            },
            timeout=args.timeout,
        )

    elapsed = time.perf_counter() - started_at
    print(f"status={response.status_code} elapsed={elapsed:.2f}s")

    try:
        payload = response.json()
    except ValueError:
        print(response.text)
        response.raise_for_status()
        return

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    response.raise_for_status()

    questions = payload.get("data", {}).get("original_questions", [])
    if len(questions) != 15:
        raise SystemExit(f"원질문 개수가 15개가 아닙니다: {len(questions)}")

    print("analyze smoke test passed: original_questions=15")


if __name__ == "__main__":
    main()
