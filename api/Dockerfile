FROM python:3.10-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (needed for simulation logic)
COPY . .
RUN chmod +x api/entrypoint.sh

# Expose API port
EXPOSE 8000

# Apply migrations before starting the single API worker.
ENTRYPOINT ["/app/api/entrypoint.sh"]
