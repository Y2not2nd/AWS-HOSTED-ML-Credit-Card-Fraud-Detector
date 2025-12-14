FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    mlflow \
    bentoml==1.4.6 \
    scikit-learn \
    joblib \
    boto3

RUN mkdir -p /app/promotion
COPY build_bento.py /app/promotion/build_bento.py

CMD ["python", "/app/promotion/build_bento.py"]
