FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    CHROMA_DIR=/data/chroma

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home appuser && mkdir -p /data && chown -R appuser:appuser /data
USER appuser

ENTRYPOINT ["sunway-rag-mcp", "--stdio"]
