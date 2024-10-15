FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["kopf", "run", "--standalone", "--namespace=darwinist", "/app/darwinist_operator.py"]