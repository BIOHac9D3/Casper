# Casper Backend - Multi-Stage Dockerfile
# Stage 1: Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update &&     apt-get install -y --no-install-recommends     build-essential     && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.12-alpine

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache     curl     git     && rm -rf /var/cache/apk/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy backend source code
COPY backend/ .

# Environment variables
ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PIP_NO_CACHE_DIR=1     PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN adduser -D casper && chown -R casper:casper /app
USER casper

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3     CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "cli.py"]
