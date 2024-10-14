FROM python:3.9-slim

WORKDIR /app

COPY api_server.py /app/api_server.py

RUN pip install fastapi uvicorn kubernetes

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]