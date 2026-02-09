# Code Review

코드 품질과 보안을 검토합니다.

## Checklist

### Security
- [ ] 하드코딩된 시크릿 없음
- [ ] PII 처리 로직 적절함
- [ ] 사용자 입력 검증됨
- [ ] .env 파일 커밋 안 됨

### Code Quality
- [ ] type hints 포함
- [ ] frozen dataclass 패턴 준수
- [ ] 결정론적 동작 (랜덤 없음)
- [ ] 에러 핸들링 적절함
- [ ] 파일 크기 800줄 이하

### Testing
- [ ] 새 기능에 테스트 있음
- [ ] 외부 의존성 mock 처리
- [ ] `python -m pytest tests/` 통과

### Style
- [ ] `from __future__ import annotations` 포함
- [ ] f-string 사용
- [ ] 불필요한 print() 없음 (cli.py 제외)
- [ ] 명확한 변수/함수 이름

### Architecture
- [ ] 단일 책임 원칙 준수
- [ ] 도메인별 패키지 구조 유지
- [ ] Playwright 브라우저 공유 패턴 유지
- [ ] 280자 제한 준수 (카드 콘텐츠)
