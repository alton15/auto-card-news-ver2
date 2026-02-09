# auto-card-news-v2

RSS 피드에서 뉴스를 가져와 Threads 캐러셀 카드 뉴스를 자동 생성합니다.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Set RSS feeds
export NEWS_RSS_FEEDS="https://feeds.bbci.co.uk/news/rss.xml"

# Generate card news
card-news generate

# Or with CLI args
card-news generate --feeds "https://example.com/rss" --output-dir ./my-output
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

## Output

Each news item produces a folder:
```
output/20260130_080000_subway-suspended/
  card_01.png  # Hook / Cover
  card_02.png  # When & Where
  card_03.png  # Impact
  card_04.png  # Key Details
  card_05.png  # What Next
  card_06.png  # CTA (Follow)
  caption.txt  # Threads caption
  metadata.json
```

## Tests

```bash
pip install pytest
pytest
```
