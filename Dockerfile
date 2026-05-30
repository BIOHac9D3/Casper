FROM python:3.12-slim

RUN apt-get update && apt-get install -y git curl

WORKDIR /app

COPY casper-node/ .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "casper-node/cli.py", "--help"]