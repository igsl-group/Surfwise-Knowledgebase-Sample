# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /srv
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir \
      "fastapi>=0.111" \
      "uvicorn[standard]>=0.30" \
      "sqlalchemy[asyncio]>=2.0.30" \
      "asyncpg>=0.29" \
      "alembic>=1.13" \
      "pydantic>=2.7" \
      "pydantic-settings>=2.3" \
      "markdown>=3.6" \
      "python-slugify>=8.0" \
      "python-multipart>=0.0.9" \
      "bleach>=6.1"

COPY . /srv

EXPOSE 8080
ENTRYPOINT ["/srv/entrypoint.sh"]
