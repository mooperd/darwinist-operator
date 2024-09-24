FROM python:3.9-slim

WORKDIR /app

COPY darwinist_operator.py /app/darwinist_operator.py

RUN pip install kopf kubernetes

CMD ["kopf", "run", "--standalone", "/app/darwinist_operator.py"]