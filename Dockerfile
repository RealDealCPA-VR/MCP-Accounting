# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MCP_SERVER_NAME=accounting-practice-mcp
ENV MCP_SERVER_VERSION=1.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server/ ./server/
COPY smithery.yaml .

# Create necessary directories
RUN mkdir -p server/data/client_profiles \
    && mkdir -p server/data/tax_tables

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash mcpuser \
    && chown -R mcpuser:mcpuser /app
USER mcpuser

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('server'); from main import AccountingMCPServer; print('Health check passed')" || exit 1

# Default command
CMD ["python", "server/main.py"]
