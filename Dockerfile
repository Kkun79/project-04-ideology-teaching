FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV APP_REGISTRATION_ENABLED=false
ENV OPENAI_API_BASE=https://api.deepseek.com/v1
ENV OPENAI_MODEL=deepseek-chat

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["sh", "-c", "python scripts/init_postgres.py && python scripts/create_admin.py && uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
