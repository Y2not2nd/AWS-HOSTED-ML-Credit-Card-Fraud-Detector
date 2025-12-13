FROM python:3.10-slim

WORKDIR /app

COPY training.py /app/training.py

RUN pip install \
    pandas \
    scikit-learn \
    mlflow \
    boto3

ENTRYPOINT ["python", "/app/training.py"]
