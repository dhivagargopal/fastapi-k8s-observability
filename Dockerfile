FROM python:3.12-slim AS builder

WORKDIR /app
COPY app/requirements.txt .

RUN python -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app/ .

CMD ["gunicorn", "-c", "gunicorn_conf.py", "main:app"]
