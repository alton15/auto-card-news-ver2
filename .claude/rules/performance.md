# Performance Rules

## Model Selection

| Task | Model | 이유 |
|------|-------|------|
| 간단한 수정/포맷팅 | Haiku | 빠르고 저렴 |
| 일반 코딩/리뷰 | Sonnet | 균형 |
| 아키텍처/복잡한 설계 | Opus | 깊은 분석 필요 |

## Context Window Management

- 불필요한 파일 읽기 최소화
- 대용량 output/ 디렉토리 탐색 자제
- 관련 파일만 선택적 읽기
- `/compact` 활용하여 컨텍스트 정리

## Application Performance

- Playwright 브라우저 인스턴스 공유 (pipeline.py 패턴 유지)
- 피드 가져오기 시 timeout 설정
- 이미지 렌더링은 배치 처리
- 불필요한 스크래핑 최소화 (RSS summary로 충분하면 스크래핑 생략 고려)
