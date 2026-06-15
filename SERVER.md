본 분석 서버의 업무 실행 프로세스는 2개이다

# 1. 유저 데이터 분석 및 원질문 생성
### 1. 유저 정보 입력
### 1-1. 포트폴리오 PDF, 깃허브 레포지토리 저장소 url, 전공(프론트/백엔드)

### 2. 포트폴리오 PDF 데이터 추출 및 정제

### 3. 포트폴리오 데이터 기반 깃허브 소스코드 추출

### 4. 포트폴리오/깃허브 데이터 기반 유저 종합 데이터 생성

### 5. 유저 종합 데이터 기반 면접 원질문 생성

# 2. 면접 피드백 생성

### 1. 면접 정보 입력
### 1-1. 면접 정보(면접 사전 설정 정보)
### 1-2. 질답 정보(질문 본문, 질문 의도, 질문 답변)

### 2. 피드백 생성
### 2-1. 종합 데이터(면접 종합 평가)
- 종합 점수
- 강점/약점
- 응답 신뢰성
- 질문 의도 적합도
- 사용빈도가 높은 단어(약 8~10개)

### 2-2. 상세데이터(각 질문별 평가)
- 꼬리질문 여부 및 단계
- 질문 본문
- 질문 의도
- 답변 본문
- 모범 답변
- 예상 꼬리질문
- 장/단점
- 피드백

---

# 현재 구현 상태 메모

## 이미 구현된 로직
- 포트폴리오 PDF 파싱 및 구조화
- GitHub 저장소 메타데이터 / README / 파일 목록 분석
- 포트폴리오 + GitHub 기반 종합 데이터(candidate_profile) 생성
- 종합 데이터를 기반으로 한 원질문 생성
- 면접 종료 후 피드백 생성

## 현재 미완료 / 미연결 사항
- `/portfolio/analyze` 는 현재 접수 ack API 형태만 남아 있고, 내부 비동기 작업 연결이 아직 없다
- `major(frontend/backend)` 를 받은 뒤 실제 background task 로 분석을 시작하는 라우터 연결이 없다
- `analysis_request_id` 를 기준으로 내부 분석 작업과 callback 을 이어주는 진입점이 없다
- callback 결과를 API 서버로 보내는 서비스 초안은 있으나 실제 라우터/작업 플로우에 연결되지 않았다
- callback 설정값(`API_SERVER_BASE_URL`, `ANALYSIS_CALLBACK_PATH`, `ANALYSIS_CALLBACK_SECRET`)은 코드 메모만 있고 config 에 아직 반영되지 않았다
- 질문은 15개 고정 생성 방향으로 정리 중이며, 현재 실제 운영 플로우와의 검증은 아직 없다

## 다음 구현 순서
1. `/portfolio/analyze` 를 `portfolio + github_url + major` 입력 접수 API로 확정
2. `analysis_request_id` 생성 후 즉시 ack 반환
3. background task 또는 동등한 비동기 실행 경로에서 분석 작업 시작
4. 포트폴리오 분석 -> GitHub 분석 -> 종합 데이터 생성 -> 원질문 15개 생성 순으로 실행
5. 결과를 `analysis_request_id + portfolio + github_repository + candidate_profile + original_questions` payload 로 callback
6. callback 서명 헤더(HMAC-SHA256) 및 재시도(최소 3회) 연결
7. 전체 플로우 E2E 검증
