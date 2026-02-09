# TDD Workflow

테스트 주도 개발 워크플로우를 실행합니다.

## Process

### 1. RED - 실패하는 테스트 작성
- 구현할 기능의 기대 동작을 테스트로 작성
- `python -m pytest tests/ -k "test_name"` 으로 실패 확인
- 테스트가 올바른 이유로 실패하는지 확인

### 2. GREEN - 최소 코드로 통과
- 테스트를 통과하는 가장 간단한 코드 작성
- 과도한 추상화나 최적화 금지
- `python -m pytest tests/` 전체 통과 확인

### 3. REFACTOR - 코드 개선
- 중복 제거, 네이밍 개선
- 테스트 통과 상태 유지 확인
- type hints 추가

## Rules

- 외부 의존성(RSS, Playwright, HTTP)은 mock 처리
- frozen dataclass 패턴 유지 (models.py 참조)
- 결정론적 동작 보장 (랜덤 사용 금지)
- 한 번에 하나의 테스트만 작성하고 통과시키기
