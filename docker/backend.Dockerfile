FROM python:3.11-slim

# Install core build dependencies for potential scikit-learn/shap extension builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency configs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source tree
COPY . .

# Bootstrap storage hierarchy subdirectories
RUN mkdir -p storage/uploads storage/ml_models storage/reports storage/agent_sessions storage/ml_shap storage/ml_registry

# Run server
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
