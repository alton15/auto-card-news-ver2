# Build Fix

빌드/테스트 에러를 수정합니다.

## Process

### 1. Identify Errors
```bash
python -m pytest tests/ -v --tb=long
```

### 2. Categorize
- **Import errors**: 모듈 경로, 순환 참조
- **Type errors**: type hints 불일치
- **Test failures**: assertion 실패, mock 설정 오류
- **Runtime errors**: Playwright, feedparser 관련

### 3. Fix Strategy
- 한 번에 하나의 에러만 수정
- 수정 후 즉시 테스트 재실행
- 연쇄적인 에러는 root cause부터 해결

### 4. Verify
```bash
python -m pytest tests/
```

## Common Issues

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError` | `pip install -e .` 재실행 |
| `PlaywrightError` | `playwright install chromium` |
| `ImportError: circular` | 지연 import 또는 구조 변경 |
| `frozen dataclass assign` | 새 인스턴스 생성으로 변경 |
