# Minimaler Container-Start für den Remote-MCP-Konnektor (`chempane.remote`).
# Baut das Python-Paket samt eingebautem UI-Bundle (`chempane/ui/dist/index.html`)
# und startet den zustandslosen Streamable-HTTP-Server als unprivilegierter Nutzer.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CHEMPANE_REMOTE_HOST=0.0.0.0 \
    CHEMPANE_REMOTE_PORT=8080

RUN useradd --create-home --shell /usr/sbin/nologin chempane

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.11 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock README.md LICENSE NOTICE THIRD_PARTY_LICENSES CHANGELOG.md ./
COPY chempane ./chempane

RUN uv sync --frozen --no-dev

USER chempane
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD .venv/bin/python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3)"

CMD [".venv/bin/python", "-m", "chempane.remote"]
