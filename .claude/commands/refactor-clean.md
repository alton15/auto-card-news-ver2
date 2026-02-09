# Refactor Clean

데드코드 분석 및 안전한 제거를 수행합니다.

## Process

### 1. Analyze
- 사용되지 않는 import 탐지
- 호출되지 않는 함수/클래스 식별
- 도달 불가능한 코드 탐지
- legacy 코드 식별 (canvas.py 등)

### 2. Categorize
- **Safe to remove**: 참조 없는 코드
- **Needs verification**: 동적으로 사용될 가능성
- **Keep**: 향후 Phase 2/3에서 사용 예정

### 3. Remove
- 한 번에 하나의 변경만 수행
- 각 제거 후 테스트 실행
- 관련 테스트도 함께 정리

### 4. Verify
```bash
python -m pytest tests/
```

## Rules

- canvas.py는 legacy로 표시되어 있으나 삭제 전 확인 필요
- `__init__.py`의 re-export는 유지
- 사용되지 않는 변수는 `_` prefix 대신 완전히 제거
