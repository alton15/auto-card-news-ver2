# Git Workflow Rules

## Commit Messages

- Conventional commits 형식 사용
- 접두사: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- 한글 커밋 메시지 허용 (한영 혼용 OK)
- 예시: `feat: Threads API 자동 업로드 기능 추가`

## Commit Checklist

1. `python -m pytest tests/` 전체 통과 확인
2. `.env` 파일이 스테이징에 포함되지 않았는지 확인
3. 불필요한 `print()` 디버그 문 제거
4. type hints 확인

## Branch Strategy

- 1인 프로젝트: main 직접 커밋 가능
- 큰 기능은 feature 브랜치 분리 권장
  - `feature/threads-api`
  - `feature/scheduler`

## What Not to Commit

- `.env` (환경변수)
- `output/` (생성된 카드 뉴스)
- `.venv/` (가상환경)
- `__pycache__/`
- `.pytest_cache/`
