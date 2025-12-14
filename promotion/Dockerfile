FROM python:3.10-slim

WORKDIR /app

# System deps (git is optional but MLflow warns without it)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    mlflow \
    bentoml \
    scikit-learn \
    joblib \
    boto3

# Copy promotion code
COPY promotion/build_bento.py /app/promotion/build_bento.py

# Default command (Airflow overrides this anyway)
CMD ["python", "/app/promotion/build_bento.py"]
