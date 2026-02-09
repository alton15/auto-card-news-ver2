# Coding Style Rules

## Python Style

- Python 3.11+ 기능 적극 활용
- `from __future__ import annotations` 모든 모듈 상단에 포함
- Type hints 필수 (함수 시그니처, 반환값)
- f-string 사용 (`.format()` 대신)

## Immutability

- 데이터 모델은 `@dataclass(frozen=True)` 사용 (models.py 패턴 준수)
- 리스트/딕셔너리 직접 변경 대신 새 객체 생성 선호
- Settings 객체 변경 시 새 인스턴스 생성

## File Organization

- 파일당 200-400줄 적정, 800줄 최대
- 도메인별 패키지 구성 (feed/, story/, render/, caption/, output/)
- 하나의 파일에 하나의 관심사
- `__init__.py`는 public API re-export 용도로만 사용

## Error Handling

- 외부 호출(HTTP, Playwright)에는 try/except 필수
- 에러 발생 시 적절한 로깅 + 복구 전략
- `sys.exit()` 사용은 cli.py에서만

## Code Quality Checklist

- [ ] type hints 포함
- [ ] docstring 작성 (public 함수/클래스)
- [ ] 하드코딩된 값 없음
- [ ] 테스트 가능한 구조
- [ ] 결정론적 동작 (랜덤 사용 금지, MD5 seed 사용)
