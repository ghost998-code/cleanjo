FROM python:3.11-alpine AS builder

WORKDIR /app

RUN apk add --no-cache build-base python3-dev linux-headers zlib-dev

COPY requirements.txt .
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache zlib

COPY --from=builder /venv /venv

COPY . .

ENV PYTHONPATH=/app
ENV PATH="/venv/bin:$PATH"
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
