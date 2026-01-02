# U²-Net Background Removal Service
# Railway-optimized Dockerfile (Debin Trixie compatible)

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (updated for Debian Trixie)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py model_loader.py ./

# Railway sets PORT automatically
ENV PORT=8000

# Expose port
EXPOSE $PORT

# Run the application (Railway will set PORT env var)
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
