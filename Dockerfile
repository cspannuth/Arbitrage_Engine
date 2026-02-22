FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD sh -c "gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT"
