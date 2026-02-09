# Checkpoint

현재 작업 상태의 체크포인트를 생성하고 검증합니다.

## Process

### 1. Verify Current State
```bash
python -m pytest tests/
```
- 모든 테스트 통과 확인

### 2. Record State
- 변경된 파일 목록 확인
- 변경 내용 요약 작성
- 남은 작업 정리

### 3. Create Checkpoint
- git status 확인
- 의미 있는 커밋 메시지로 커밋
- 테스트 통과 상태에서만 커밋

## Checkpoint Format

```markdown
## Checkpoint: [작업명]

### 완료된 작업
- [완료 항목]

### 변경 파일
- [파일 목록]

### 남은 작업
- [미완료 항목]

### 테스트 상태
- 전체: X/Y 통과
```
