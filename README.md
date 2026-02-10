# auto-card-news-v2

RSS 피드에서 뉴스를 가져와 Threads 캐러셀 카드 뉴스(PNG + 캡션)를 자동 생성하고 발행하는 Python CLI 도구.

## Architecture

### Pipeline Flow

```
                          ┌──────────────────────────────────────────────┐
                          │               card-news generate             │
                          └──────────────┬───────────────────────────────┘
                                         │
                    ┌────────────────────┐│┌────────────────────┐
                    │  RSS Feed 1 (XML)  │││  RSS Feed N (XML)  │
                    └────────┬───────────┘│└──────────┬─────────┘
                             │            │           │
                             ▼            ▼           ▼
                  ┌──────────────────────────────────────────────┐
                  │  feed/fetcher.py  — HTTP fetch (urllib)      │
                  │  feed/parser.py   — feedparser로 파싱        │
                  └──────────────────────┬───────────────────────┘
                                         │ list[FeedItem]
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │  feed/dedup.py    — URL 기반 중복 제거       │
                  │  feed/history.py  — 발행 이력 필터링 (영구)  │
                  └──────────────────────┬───────────────────────┘
                                         │ list[FeedItem] (deduplicated)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │  feed/scraper.py  — Playwright로 본문 스크랩 │
                  └──────────────────────┬───────────────────────┘
                                         │ FeedItem (full_text 포함)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │  story/summarizer.py — 구조화된 Story 생성   │
                  │  story/safety.py     — PII 제거              │
                  └──────────────────────┬───────────────────────┘
                                         │ Story
                               ┌─────────┴─────────┐
                               ▼                     ▼
              ┌─────────────────────────┐ ┌─────────────────────────┐
              │  render/                │ │  caption/               │
              │  card_builder → 6 cards │ │  composer.py            │
              │  carousel.py            │ │  engagement.py          │
              │  → Playwright screenshot│ │  hashtags.py            │
              │  → PNG x 6 (1080x1350) │ │  → caption text         │
              └───────────┬─────────────┘ └────────────┬────────────┘
                          │                            │
                          ▼                            ▼
                  ┌──────────────────────────────────────────────┐
                  │  output/packager.py — PNG + caption + meta   │
                  └──────────────────────┬───────────────────────┘
                                         │ ThreadsPost
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │  feed/history.py  — 발행 URL 이력 저장       │
                  └──────────────────────┬───────────────────────┘
                                         │
                              (--auto-publish 시)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │  threads/                                    │
                  │  image_host.py  — Cloudinary 업로드          │
                  │  client.py      — Threads Graph API          │
                  │  publisher.py   — 업로드 → 발행 → 정리      │
                  └──────────────────────────────────────────────┘
```

### Data Models

```
FeedItem          Story              CardContent         ThreadsPost
├─ title          ├─ hook_title      ├─ title            ├─ image_paths (PNG x6)
├─ url            ├─ what_happened   ├─ body             ├─ caption
├─ summary        ├─ where_when      ├─ card_index       ├─ metadata
├─ published_at   ├─ impact          ├─ card_total       └─ output_dir
├─ source_domain  ├─ key_details     ├─ header
└─ full_text      ├─ what_next       └─ footer
                  ├─ tags
                  ├─ source_domain
                  ├─ source_url
                  └─ published_at
```

All models are `@dataclass(frozen=True)` — immutable after creation.

### Directory Structure

```
src/auto_card_news_v2/
  models.py            # FeedItem, Story, CardContent, ThreadsPost
  config.py            # Settings (env vars → frozen dataclass)
  cli.py               # argparse CLI entrypoint
  pipeline.py          # run_pipeline() 전체 오케스트레이션
  runner.py            # APScheduler 기반 주기 실행 (Docker용)
  scheduler.py         # cron 기반 스케줄러 (로컬용)
  feed/
    fetcher.py         # RSS XML 다운로드
    parser.py          # feedparser → FeedItem 변환
    dedup.py           # 실행 내 URL 중복 제거
    history.py         # 실행 간 발행 이력 (영구 저장)
    scraper.py         # Playwright 본문 스크래핑
  story/
    summarizer.py      # FeedItem → Story 구조화
    safety.py          # PII(이메일, 전화번호 등) 제거
  render/
    card_builder.py    # Story → CardContent x 6
    carousel.py        # HTML/CSS → Playwright → PNG
    theme.py           # 색상, 레이아웃 설정
    canvas.py          # legacy (미사용)
    typography.py      # 폰트 설정 (Inter + Noto Sans KR)
    templates/
      card.html        # Jinja2 카드 템플릿
  caption/
    composer.py        # Story → Threads 캡션 텍스트
    engagement.py      # hook, CTA 생성
    hashtags.py        # 태그 → 해시태그 변환
  output/
    packager.py        # PNG + caption + metadata.json 패키징
  threads/
    token_store.py     # 토큰 저장/로드/갱신
    image_host.py      # Cloudinary 업로드/삭제
    client.py          # Threads Graph API 호출
    publisher.py       # 전체 발행 플로우
Dockerfile             # 멀티스테이지 Docker 빌드
docker-compose.yml     # Docker Compose 서비스 정의
tests/                 # pytest (88개 테스트)
```

## Setup

### 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

### Docker 실행

```bash
cp .env.example .env   # 환경변수 설정
# .env 파일에 필요한 값 입력

docker compose build
docker compose up -d
docker compose logs -f
```

## Usage

### CLI 명령어

```bash
# 카드 뉴스 생성
card-news generate --feeds "https://en.yna.co.kr/RSS/news.xml" --limit 3

# 미리보기 (파일 생성 없이)
card-news generate --dry-run

# 생성 + Threads 자동 발행
card-news generate --auto-publish --limit 1

# Threads 토큰 등록
card-news auth --token "YOUR_TOKEN"

# 기존 output 수동 발행
card-news publish output/20260130_080000_subway-suspended/

# 스케줄러 실행 (Docker 컨테이너용)
card-news run --interval 60 --limit 1
card-news run --no-publish              # 발행 없이 생성만
card-news run --interval 30 --limit 3   # 30분 간격, 3개씩

# cron 스케줄 관리 (로컬용)
card-news schedule install --times "12:00,15:00,17:00" --limit 1
card-news schedule status
card-news schedule uninstall
```

### Docker Compose

```bash
# 빌드 + 백그라운드 실행
docker compose up -d

# 로그 확인
docker compose logs -f

# dry-run 테스트
docker compose run --rm card-news generate --dry-run

# 중지 / 재시작 (토큰·이력 유지)
docker compose down
docker compose up -d
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEWS_RSS_FEEDS` | (required) | Comma-separated RSS feed URLs |
| `NEWS_OUTPUT_DIR` | `./output` | Output directory |
| `NEWS_SAFETY_ENABLED` | `true` | PII redaction and safety filters |
| `NEWS_MAX_ITEMS` | `10` | Max items per run |
| `NEWS_NUM_CARDS` | `6` | Cards per carousel |
| `NEWS_BRAND_NAME` | `Card News` | Brand name on CTA card |
| `NEWS_BRAND_HANDLE` | `@cardnews` | Handle on CTA card |
| `NEWS_SCHEDULE_INTERVAL` | `60` | Scheduler interval (minutes) |
| `NEWS_AUTO_PUBLISH` | `true` | Auto-publish to Threads |
| `NEWS_TIMEZONE` | `Asia/Seoul` | Scheduler timezone |
| `THREADS_USER_ID` | | Threads user ID (발행 시 필요) |
| `CLOUDINARY_CLOUD_NAME` | | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | | Cloudinary API secret |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` | | Custom Chromium path (ARM64 등) |

## Output

Each news item produces a folder:
```
output/20260130_080000_subway-suspended/
  card_01.png    # Hook / Cover
  card_02.png    # When & Where
  card_03.png    # Impact
  card_04.png    # Key Details
  card_05.png    # What Next
  card_06.png    # CTA (Follow)
  caption.txt    # Threads caption
  metadata.json
```

## Key Design Decisions

- **Deterministic** — 동일 입력 → 동일 출력 (MD5 seed, 랜덤 없음)
- **Shared Playwright** — 스크래핑과 렌더링이 동일 브라우저 인스턴스 공유
- **PII removal** — placeholder 대신 빈 문자열 대체
- **Persistent dedup** — `~/.card-news/publish_history.json`으로 실행 간 중복 방지
- **Dual scheduler** — 로컬 crontab 또는 Docker 내 APScheduler 선택 가능
- **Docker ready** — 멀티스테이지 빌드, 비루트 유저, ARM64 호환

## Docker Architecture

```
docker-compose.yml
├── card-news (container)
│   ├── APScheduler (BlockingScheduler)
│   │   └── run_job() → pipeline + publish (interval마다 반복)
│   ├── Playwright Chromium (/opt/playwright)
│   └── fonts-noto-cjk (한국어 폰트)
├── card-news-data (volume)        # ~/.card-news/ (토큰 + 발행 이력)
└── ./output (bind mount)          # 생성된 카드뉴스 PNG
```

## Tests

```bash
python -m pytest tests/        # 전체 실행 (88개)
python -m pytest tests/ -v     # 상세 출력
python -m pytest tests/ -k "test_history"  # 특정 테스트
```
