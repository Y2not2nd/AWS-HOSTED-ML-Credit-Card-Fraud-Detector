FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY service.py .

# Copy model artifact
COPY credit_fraud_model.bentomodel /tmp/credit_fraud_model.bentomodel

# Import model into container BentoML store
RUN bentoml models import /tmp/credit_fraud_model.bentomodel

EXPOSE 3000
 
CMD ["bentoml", "serve", "service:svc", "--host", "0.0.0.0", "--port", "3000"]
