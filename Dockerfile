# Use official Python 3.10 slim base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files & enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system build dependencies and ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Layer 1: Install torch CPU-only wheel first (cached separately so rebuilds don't re-download it)
# This avoids the default PyPI torch wheel which is 500MB+ (GPU build).
RUN pip install --no-cache-dir --default-timeout=120 \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

# Layer 2: Install remaining requirements (this layer rebuilds when requirements.txt changes,
# but the torch layer above is reused from cache)
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

# Copy application source code
COPY app/ /app/app/

# Expose FastAPI backend port
EXPOSE 8000

# Default command to run the backend API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
