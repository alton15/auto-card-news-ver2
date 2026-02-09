# auto-card-news-ver2

RSS 피드에서 한국 뉴스를 영어로 가져와 Threads 캐러셀 카드 뉴스(PNG + 캡션)를 자동 생성하는 Python CLI 도구.

## Tech Stack

- **Python** 3.11+ / **Build**: hatchling (src layout)
- **Playwright**: 기사 스크래핑 + HTML/CSS 렌더링 (공유 브라우저)
- **Jinja2**: HTML/CSS 카드 템플릿 (Inter + Noto Sans KR)
- **feedparser**: RSS/Atom 피드 파싱
- **Pillow**: legacy canvas (현재 미사용)
- **pytest**: 테스트 프레임워크

## Architecture

```
FeedItem (RSS + scraping)
  -> Story (heuristic summarizer + PII redaction)
    -> CardContent x 5 (card_builder)
      -> PNG x 5 (HTML/CSS + Playwright screenshot, 1080x1350px)
    -> Caption (hook + bullets + CTA + hashtags)
      -> ThreadsPost (images + caption + metadata.json)
```

## Directory Structure

```
src/auto_card_news_v2/
  models.py        # FeedItem, Story, CardContent, ThreadsPost (frozen dataclass)
  config.py        # Settings (env vars)
  cli.py           # argparse CLI: card-news generate
  pipeline.py      # run_pipeline() - 전체 오케스트레이션
  feed/            # fetcher, parser, dedup, scraper
  story/           # summarizer, safety (PII redaction)
  render/          # carousel, card_builder, theme, canvas, typography, templates/
  caption/         # composer, engagement, hashtags
  output/          # packager
tests/             # pytest 테스트 (26개)
```

## Critical Rules

### 1. Code Organization

- src layout 사용 (`src/auto_card_news_v2/`)
- 도메인별 하위 패키지 구성 (feed/, story/, render/, caption/, output/)
- 파일당 200-400줄 목표, 800줄 최대
- frozen dataclass로 불변 데이터 모델 유지

### 2. Code Style

- Type hints 필수 (`from __future__ import annotations`)
- `print()` 대신 `logging` 모듈 사용 (cli.py 제외)
- 하드코딩된 시크릿 절대 금지 - 환경변수 사용
- PII 처리 시 safety.py 통해 반드시 sanitize

### 3. Design Decisions

- **결정론적**: 동일 입력 -> 동일 출력 (MD5 seed, 랜덤 없음)
- **Playwright 공유**: 스크래핑과 렌더링이 동일 브라우저 인스턴스 사용
- **PII 완전 제거**: placeholder 대신 빈 문자열로 대체
- **280자 제한**: 각 카드 섹션 최대 280자
- **한영 이중 지원**: 불용어, 폰트, 주의문구 양언어 대응

### 4. Testing

- `python -m pytest tests/` 로 실행
- 새 기능 추가 시 반드시 테스트 작성
- 외부 의존성(RSS, Playwright)은 mock 처리

### 5. Security

- .env 파일 커밋 금지
- PII(이메일, 전화번호, 주민번호, 주소) 자동 제거 활성화
- 사용자 입력(RSS URL 등) 검증 필수

## Environment Variables

```bash
NEWS_RSS_FEEDS=https://en.yna.co.kr/RSS/news.xml,...
NEWS_OUTPUT_DIR=./output
NEWS_SAFETY_ENABLED=true
NEWS_MAX_ITEMS=10
NEWS_NUM_CARDS=6
NEWS_BRAND_NAME=Card News
NEWS_BRAND_HANDLE=@cardnews
```

## Running

```bash
pip install -e .
playwright install chromium
python -m pytest tests/
card-news generate
card-news generate --dry-run
card-news generate --feeds "URL" --limit 3
```

## Available Commands

- `/tdd` - 테스트 주도 개발 워크플로우
- `/plan` - 구현 계획 수립
- `/code-review` - 코드 리뷰
- `/build-fix` - 빌드/타입 에러 수정
- `/refactor-clean` - 데드코드 정리
- `/verify` - 전체 검증
- `/learn` - 세션에서 패턴 추출
- `/checkpoint` - 체크포인트 생성

## Git Workflow

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- 한글 커밋 메시지 가능 (한영 혼용 OK)
- main 직접 커밋 가능 (1인 프로젝트)
- 모든 테스트 통과 후 커밋
