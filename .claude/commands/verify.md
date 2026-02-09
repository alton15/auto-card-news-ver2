# Verify

프로젝트 전체 검증을 수행합니다.

## Checklist

### 1. Tests
```bash
python -m pytest tests/ -v
```
- 모든 테스트 통과 확인
- 새로 추가된 코드에 테스트 있는지 확인

### 2. Import Check
- 순환 import 없음
- 사용되지 않는 import 없음

### 3. Security
- `.env` 파일 커밋되지 않음
- 하드코딩된 시크릿 없음
- PII 처리 로직 정상 작동

### 4. Architecture
- src layout 구조 유지
- 도메인별 패키지 분리 유지
- frozen dataclass 패턴 유지

### 5. Configuration
- `pyproject.toml` 의존성 정확
- `pip install -e .` 정상 작동
- `card-news` CLI 명령어 작동

### 6. Output Quality
```bash
card-news generate --dry-run
```
- dry-run 정상 작동 확인
