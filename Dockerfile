FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will assign via PORT env var)
EXPOSE 8000

# Health check - use PORT env var if set, otherwise default to 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/ || exit 1

# Run application - use PORT env var if set, otherwise default to 8000
CMD uvicorn api_websocket:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
