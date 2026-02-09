# Agent Delegation Rules

## Available Agents

| Agent | 용도 | 사용 시점 |
|-------|------|-----------|
| planner | 구현 계획 수립 | 새 기능, 리팩토링 시작 전 |
| code-reviewer | 코드 품질 리뷰 | PR 또는 주요 변경 후 |
| security-reviewer | 보안 취약점 분석 | config, safety, scraper 변경 시 |
| tdd-guide | TDD 워크플로우 | 새 기능 개발 시 |
| build-error-resolver | 빌드 에러 해결 | pytest/import 에러 발생 시 |
| refactor-cleaner | 데드코드 정리 | 리팩토링, 정리 작업 시 |

## When to Delegate

- **복잡한 기능 구현**: planner -> tdd-guide -> code-reviewer 순서
- **보안 관련 변경**: security-reviewer 반드시 실행
- **빌드 실패**: build-error-resolver에 위임
- **코드 정리**: refactor-cleaner 실행

## Parallel Execution

독립적인 작업은 병렬 실행 가능:
- security-reviewer + code-reviewer (동시 리뷰)
- 서로 다른 모듈의 테스트 작성
