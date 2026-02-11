# Stage 1: Build wheels
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# Stage 2: Runtime
FROM python:3.11-slim-bookworm

# Chromium runtime dependencies + Korean fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash cardnews

WORKDIR /app

# Install wheels + playwright chromium in shared location
COPY --from=builder /wheels /wheels

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

RUN pip install --no-cache-dir /wheels/*.whl \
    && rm -rf /wheels \
    && playwright install chromium \
    && playwright install-deps chromium \
    && chmod -R o+rx /opt/playwright

# Create output + data directories owned by cardnews
RUN mkdir -p /app/output /home/cardnews/.card-news \
    && chown cardnews:cardnews /app/output /home/cardnews/.card-news

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER cardnews

ENV PYTHONUNBUFFERED=1
ENV NEWS_OUTPUT_DIR=/app/output

HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python -c "import auto_card_news_v2"

ENTRYPOINT ["/entrypoint.sh", "card-news"]
CMD ["run", "--interval", "60", "--limit", "1"]
