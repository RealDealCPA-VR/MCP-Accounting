FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p server/data/client_profiles \
    && mkdir -p server/data/tax_tables

# Set environment variables
ENV PYTHONPATH=/app

# Expose port for HTTP server
EXPOSE 8080

# Run the HTTP wrapper server
CMD ["python", "server/http_server.py"]
