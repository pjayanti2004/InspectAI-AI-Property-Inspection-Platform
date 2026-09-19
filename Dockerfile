# InspectAI — Production Dockerfile
# Multi-stage build for minimal image size and security.

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -r inspectai && useradd -r -g inspectai inspectai

# Create directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/streamlit_app/uploads && \
    chown -R inspectai:inspectai /app

# Copy application code
COPY --chown=inspectai:inspectai streamlit_app/ streamlit_app/
COPY --chown=inspectai:inspectai docs/ docs/

# Switch to non-root user
USER inspectai

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Environment variables (overridable at runtime)
ENV GEMINI_API_KEY="" \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    DATABASE_PATH=/app/data/inspectai.db \
    MAX_UPLOAD_MB=15 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_MAX_UPLOAD_SIZE=15 \
    STREAMLIT_BROWSER_SERVER_ADDRESS=0.0.0.0

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app/app.py"]
