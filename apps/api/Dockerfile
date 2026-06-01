FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/services/parser

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/api/app /app/app
COPY apps/api/alembic.ini /app/apps/api/alembic.ini
COPY apps/api/migrations /app/apps/api/migrations
COPY services/parser /app/services/parser

EXPOSE 8000

CMD ["sh", "-c", "alembic -c apps/api/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
