# ==========================================
# Stage 1: Production Base
# ==========================================
FROM python:3.12-slim as production

# Install system dependencies
# ffmpeg: required for audio processing (pydub)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=soundboard.py

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --group appuser

# Create necessary directories and set permissions
# We need write access to:
# - app/static/uploads (for user content)
# - logs (for app logs)
# - . (for sqlite databases if created at runtime)
RUN mkdir -p app/static/uploads logs && \
    chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appgroup . .

# Expose port
EXPOSE 8000

# Default command: Production Gunicorn Server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "soundboard:app"]


# ==========================================
# Stage 2: Test & Troubleshooting Base
# ==========================================
# We use the official Playwright image which includes browsers and system deps
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy as test

WORKDIR /app

# Install system dependencies (FFmpeg is still needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# We run as root in the test container to facilitate
# installing extra debug tools if needed interactively.
# (Security is less of a concern in a transient test container)

# Default command: Run Tests
CMD ["pytest", "tests/"]
