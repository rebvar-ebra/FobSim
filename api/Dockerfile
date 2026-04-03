FROM python:3.10-slim

WORKDIR /app

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

# Expose API port
EXPOSE 8000

# Start server using the API directory as module path
CMD ["python3", "api/server.py"]
