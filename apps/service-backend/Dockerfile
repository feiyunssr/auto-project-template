FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/service-backend/pyproject.toml /app/pyproject.toml
COPY apps/service-backend/app /app/app

RUN pip install --no-cache-dir .

EXPOSE 11010

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "11010"]
