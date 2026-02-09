# Testing Rules

## Framework

- **pytest** 사용 (`python -m pytest tests/`)
- `pyproject.toml`에 설정: `addopts = "-q"`, `testpaths = ["tests"]`

## Test Structure

```
tests/
  test_models.py       # 데이터 모델 검증
  test_feed_*.py       # 피드 관련 테스트
  test_story_*.py      # 스토리 요약/안전성 테스트
  test_render_*.py     # 렌더링 테스트
  test_caption_*.py    # 캡션 생성 테스트
  test_pipeline.py     # 통합 테스트
```

## Guidelines

1. **새 기능 = 새 테스트**: 기능 추가 시 반드시 테스트 작성
2. **Mock 외부 의존성**: RSS 피드, Playwright, HTTP 요청은 mock 처리
3. **결정론적 테스트**: 랜덤 없이 동일 입력 -> 동일 결과
4. **단위 테스트 우선**: 개별 함수/모듈 단위로 테스트
5. **경계값 테스트**: 빈 입력, 긴 텍스트, 특수문자 등

## TDD Workflow

1. **RED**: 실패하는 테스트 먼저 작성
2. **GREEN**: 테스트 통과하는 최소 코드 작성
3. **REFACTOR**: 코드 정리 (테스트 통과 상태 유지)

## Running Tests

```bash
python -m pytest tests/           # 전체 실행
python -m pytest tests/ -v        # 상세 출력
python -m pytest tests/ -k "test_name"  # 특정 테스트
python -m pytest tests/ --tb=short      # 간단한 트레이스백
```

## Test Quality

- assertion 메시지 포함 권장
- fixture 활용하여 중복 설정 제거
- 테스트 이름은 `test_기능_상황_기대결과` 패턴
