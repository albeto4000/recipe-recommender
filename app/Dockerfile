FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev

COPY . .

# RUN uv run download_models.py


FROM python:3.13-slim

RUN useradd -m -r appuser

WORKDIR /app

COPY --from=builder \
     --chown=appuser:appuser \
     /app/.venv \
     /app/.venv
# COPY --from=builder \
#      --chown=appuser:appuser \
#      /app/models \
#      /app/models
COPY --chown=appuser:appuser . .

RUN chown -R appuser:appuser /app

RUN chmod 755 /app && chmod 664 /app/db.sqlite3

ENV PATH="/app/.venv/bin:$PATH"
ENV SECRET_KEY="django-insecure-lrpnak(w(#@&-6myzn%+182m!xb2)5r43!n1l&hmg87!4r7p4a"
ENV DEBUG=True

USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi:application"]