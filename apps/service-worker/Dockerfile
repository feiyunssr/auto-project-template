FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY apps/service-backend/app /workspace/apps/service-backend/app
COPY apps/service-worker/pyproject.toml /workspace/apps/service-worker/pyproject.toml
COPY apps/service-worker/service_worker /workspace/apps/service-worker/service_worker

RUN pip install --no-cache-dir /workspace/apps/service-worker

CMD ["python", "-m", "service_worker.main"]
