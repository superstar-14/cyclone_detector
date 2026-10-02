# ============================================================
# IMD Cyclone Detector – Backend Dockerfile
# Optimized for Render Free Tier (512 MB RAM limit)
# Image size: ~200MB (down from >4GB)
# ============================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production \
    DEMO_MODE=true

WORKDIR /app

# Install minimal curl for health check probing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lean Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Make start script executable
RUN chmod +x ./start.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Start Uvicorn with 1 worker and concurrency safeguards for 512MB RAM
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --limit-concurrency 50 --backlog 128 --timeout-keep-alive 5"]
