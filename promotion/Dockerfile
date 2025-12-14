FROM python:3.10-slim

WORKDIR /app

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps (PINNED)
RUN pip install --no-cache-dir \
    mlflow==2.11.3 \
    bentoml==1.4.6 \
    scikit-learn==1.4.2 \
    joblib==1.4.2 \
    boto3==1.34.34

# Log versions at build time (for traceability)
RUN python - <<EOF
import bentoml, mlflow, sklearn, joblib, boto3, sys
print("Python:", sys.version)
print("BentoML:", bentoml.__version__)
print("MLflow:", mlflow.__version__)
print("sklearn:", sklearn.__version__)
print("joblib:", joblib.__version__)
print("boto3:", boto3.__version__)
EOF

# App code
RUN mkdir -p /app/promotion
COPY build_bento.py /app/promotion/build_bento.py

# Runtime entrypoint
CMD ["python", "/app/promotion/build_bento.py"]
