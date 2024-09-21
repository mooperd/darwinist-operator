FROM python:3.9-slim

WORKDIR /app

COPY operator.py /app/operator.py

RUN pip install kopf kubernetes

CMD ["kopf", "run", "--standalone", "/app/operator.py"]