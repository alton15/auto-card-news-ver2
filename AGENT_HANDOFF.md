# Agent Handoff: auto-card-news-ver2

## Project Overview

RSS 피드에서 한국 뉴스를 영어로 가져와 Threads 캐러셀 카드 뉴스(PNG 이미지 + 캡션)를 자동 생성하는 Python CLI 도구.

- **목적**: 한국의 주요 이슈를 영어로 소개하는 Threads 계정 운영
- **현재 상태**: Phase 1 완료 (이미지 + 캡션 생성, 수동 업로드)
- **Python**: 3.11+ / **Build**: hatchling (src layout)
- **테스트**: pytest 26개 전체 통과

## Architecture

```
FeedItem (RSS + scraping)
  → Story (heuristic summarizer + PII redaction)
    → CardContent × 5 (card_builder)
      → PNG × 5 (HTML/CSS + Playwright screenshot, 1080×1350px)
    → Caption (hook + bullets + CTA + hashtags)
      → ThreadsPost (images + caption + metadata.json)
```

**핵심 기술 스택**: feedparser, Playwright (스크래핑 + 렌더링 공유 브라우저), Jinja2 HTML/CSS 템플릿, Pillow (legacy canvas)

## Directory Structure

```
src/auto_card_news_v2/
├── models.py          # FeedItem, Story, CardContent, ThreadsPost (frozen dataclass)
├── config.py          # Settings (env vars: NEWS_RSS_FEEDS, NEWS_OUTPUT_DIR 등)
├── cli.py             # argparse CLI: card-news generate [--feeds|--output-dir|--dry-run|--limit]
├── pipeline.py        # run_pipeline() - 전체 오케스트레이션 (Playwright 브라우저 공유)
├── feed/
│   ├── fetcher.py     # HTTP fetch (urllib + certifi)
│   ├── parser.py      # RSS/Atom → FeedItem (feedparser + fallback XML)
│   ├── dedup.py       # URL 중복 제거
│   └── scraper.py     # 기사 본문 스크래핑 (Playwright, 다중 CSS 셀렉터)
├── story/
│   ├── summarizer.py  # FeedItem → Story (휴리스틱: 노이즈 필터, 280자 제한, 정보밀도 점수)
│   └── safety.py      # PII 제거 (이메일, 전화번호, 주민번호, 주소) + 주의 문구
├── render/
│   ├── carousel.py    # HTML/CSS → Playwright screenshot → PNG (render_carousel_with_browser)
│   ├── card_builder.py # Story → CardContent × 5 (cover/impact/bullets/what_next/cta)
│   ├── theme.py       # Theme.dark() / Theme.light(), css_vars() for Jinja2
│   ├── canvas.py      # PIL 기반 드로잉 (legacy, 현재 미사용)
│   ├── typography.py  # 폰트 로드/캐싱, CJK 텍스트 래핑
│   └── templates/card.html  # Jinja2 HTML/CSS 카드 템플릿 (Inter + Noto Sans KR)
├── caption/
│   ├── composer.py    # hook + title + bullets + source + CTA + question + hashtags
│   ├── engagement.py  # 결정론적 hook/CTA/question 선택 (MD5 seed)
│   └── hashtags.py    # 카테고리 감지 + 태그 생성 (5-8개)
└── output/
    └── packager.py    # 타임스탬프 폴더 생성 + PNG/caption.txt/metadata.json 저장
```

## Configuration (.env)

```bash
NEWS_RSS_FEEDS=https://en.yna.co.kr/RSS/news.xml,http://rss.joinsmsn.com/news/joins_joongangdaily_news.xml
NEWS_OUTPUT_DIR=./output
NEWS_SAFETY_ENABLED=true
NEWS_MAX_ITEMS=10
NEWS_NUM_CARDS=6
NEWS_BRAND_NAME=Card News
NEWS_BRAND_HANDLE=@cardnews
```

## Pipeline Flow (pipeline.py)

1. `_fetch_all_feeds()` → RSS 피드 가져오기 + 파싱
2. `deduplicate()` → URL 중복 제거
3. `sync_playwright()` context manager로 Chromium 브라우저 1개 실행
4. 각 FeedItem에 대해:
   - `scrape_article(url, browser)` → full_text 추출 (실패 시 RSS summary 사용)
   - `build_story(item)` → 휴리스틱 요약
   - `sanitize_story()` → PII 제거
   - `render_carousel_with_browser()` → PNG 5장 생성
   - `compose_caption()` → 캡션 생성
   - `package_output()` → 폴더에 저장
5. 브라우저 종료, `list[ThreadsPost]` 반환

## Card Structure (5 cards)

| # | Type | Content | Visual |
|---|------|---------|--------|
| 1 | cover | what_happened | 그라디언트 텍스트, 큰 폰트 |
| 2 | body | impact | 표준 본문 |
| 3 | bullets | key_details × 4 | 불릿 리스트 |
| 4 | body | what_next | 표준 본문 |
| 5 | cta | brand + handle | 브랜드 + 팔로우 버튼 |

## Key Design Decisions

- **결정론적**: 동일 입력 → 동일 출력 (MD5 seed, 랜덤 없음)
- **Playwright 공유**: 스크래핑과 렌더링이 동일 브라우저 인스턴스 사용
- **PII 완전 제거**: placeholder 대신 빈 문자열로 대체 (카드에 [email] 표시 방지)
- **노이즈 필터링**: 바이라인, 사진 크레딧, 저작권 등 정규식 패턴 제거
- **정보밀도 점수**: key_details 선택 시 숫자(+2), 인용(+1.5) 가중치
- **280자 제한**: 각 카드 섹션 최대 280자
- **한영 이중 지원**: 불용어, 폰트, 주의문구 모두 양언어 대응

## Known Issues & Workarounds

| Issue | Solution |
|-------|----------|
| JoongAng Daily RSS 404 | `http://rss.joinsmsn.com/news/joins_joongangdaily_news.xml` 사용 |
| HTML entity 이중 이스케이프 (`&amp;apos;`) | `html.unescape()` → `html.escape()` 순서로 처리 |
| canvas.py (PIL 기반) | legacy 코드, 현재 carousel.py가 HTML/CSS 렌더링 사용 |

## Planned Future Work

- **Phase 2**: Threads API 연동 → 자동 업로드
- **Phase 3**: cron/스케줄러 → 주기적 자동 생성 + 업로드
- 디자인 추가 개선 (CSS 커스터마이징)

## Running

```bash
cd auto-card-news-ver2

# Install
pip install -e .
playwright install chromium

# Test
python -m pytest tests/

# Generate
card-news generate
card-news generate --dry-run
card-news generate --feeds "https://en.yna.co.kr/RSS/news.xml" --limit 3
```

## Output Example

```
output/20260202_015241_lotte-hyundai-selected-as-new-duty-free-/
├── card_01.png ~ card_05.png
├── caption.txt
└── metadata.json
```
