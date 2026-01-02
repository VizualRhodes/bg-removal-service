# U²-Net Background Removal Service
# Railway-optimized Dockerfile

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py model_loader.py ./

# Railway sets PORT automatically, but we'll use it
ENV PORT=8000

# Expose port (Railway will map this)
EXPOSE $PORT

# Run the application
# Railway sets PORT env var, but uvicorn defaults to 8000
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
