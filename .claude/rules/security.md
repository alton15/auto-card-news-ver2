# Security Rules

## Mandatory Checks

1. **No hardcoded secrets** - API 키, 비밀번호, 토큰을 코드에 직접 작성 금지
2. **환경변수 사용** - 민감한 설정은 반드시 `.env` 또는 환경변수로 관리
3. **.env 커밋 금지** - `.gitignore`에 `.env` 포함 확인
4. **사용자 입력 검증** - RSS URL, CLI 인자 등 외부 입력은 반드시 검증
5. **PII 보호** - `story/safety.py`의 `sanitize_story()` 반드시 적용

## PII Handling

- 이메일, 전화번호, 주민번호, 주소 패턴 자동 탐지/제거
- placeholder 텍스트(`[email]`) 대신 빈 문자열로 대체
- `NEWS_SAFETY_ENABLED=true` 기본값 유지

## Dependency Security

- 의존성 추가 시 신뢰할 수 있는 패키지만 사용
- `pip audit` 또는 `safety check`으로 취약점 스캔 권장
- Playwright 버전 업데이트 시 호환성 확인

## File System Security

- 사용자 제공 경로에 대해 path traversal 방지
- output 디렉토리 생성 시 적절한 권한 설정
- 임시 파일 사용 후 정리

## Security Review Triggers

다음 파일 변경 시 보안 리뷰 필수:
- `config.py` (설정/환경변수)
- `safety.py` (PII 처리)
- `scraper.py` (외부 URL 접근)
- `fetcher.py` (HTTP 요청)
