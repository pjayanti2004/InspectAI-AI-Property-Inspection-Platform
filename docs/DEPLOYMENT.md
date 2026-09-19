# InspectAI — Deployment Guide

## Overview

InspectAI is a Streamlit application that can be deployed locally, on a VPS, or on a cloud platform. This guide covers the most common deployment options.

## Inspection Workflow

```mermaid
graph LR
    A["User visits app"] --> B["Enter property details"]
    B --> C["Upload images"]
    C --> D["Review & confirm"]
    D --> E["AI processing<br/>(CV + Gemini)"]
    E --> F["View report"]
    F --> G["Download PDF"]

    style E fill:#F59E0B,color:#fff
    style G fill:#10B981,color:#fff
```

## Architecture Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.10+ |
| Memory | 2GB minimum (4GB recommended for batch processing) |
| Disk | 500MB for app + dependencies |
| Network | Outbound HTTPS to `generativelanguage.googleapis.com` |
| Browser | Modern browser with JavaScript enabled |

## Local Deployment

### Using Streamlit directly

```bash
# Clone and setup
git clone https://github.com/<your-username>/inspectai.git
cd inspectai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run
streamlit run streamlit_app/app.py --server.port 8501
```

### Using systemd (Linux VPS)

Create `/etc/systemd/system/inspectai.service`:

```ini
[Unit]
Description=InspectAI Streamlit Application
After=network.target

[Service]
Type=simple
User=inspectai
WorkingDirectory=/opt/inspectai
Environment="PATH=/opt/inspectai/.venv/bin"
EnvironmentFile=/opt/inspectai/.env
ExecStart=/opt/inspectai/.venv/bin/streamlit run streamlit_app/app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable inspectai
sudo systemctl start inspectai
sudo systemctl status inspectai
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY streamlit_app/ streamlit_app/
COPY docs/ docs/

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8501

# Run
ENV GEMINI_API_KEY=""
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose

```yaml
version: "3.8"

services:
  inspectai:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - INSPECTAI_DB_PATH=/app/data/inspectai.db
      - INSPECTAI_LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

```bash
docker compose up -d
```

## Cloud Deployment

### Streamlit Community Cloud

1. Push your repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set the entry point: `streamlit_app/app.py`
5. Add `GEMINI_API_KEY` in the Secrets section

**Limitations:**
- No persistent disk (database resets on deploy)
- 1GB RAM limit
- App sleeps after inactivity

### Railway

1. Connect GitHub repo
2. Add `GEMINI_API_KEY` environment variable
3. Set start command: `streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0`
4. Add persistent volume for `data/` directory

### Render

1. Create a new Web Service
2. Connect GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run streamlit_app/app.py --server.port $PORT --server.address 0.0.0.0`
5. Add environment variables

### AWS EC2

```bash
# On EC2 instance (Ubuntu)
sudo apt update && sudo apt install -y python3.11 python3.11-venv nginx

# Clone and setup
git clone https://github.com/<your-username>/inspectai.git
cd inspectai
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure nginx as reverse proxy
sudo tee /etc/nginx/sites-available/inspectai << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/inspectai /etc/nginx/sites-enabled/
sudo systemctl reload nginx

# Run with systemd (see above)
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google Gemini API key |
| `INSPECTAI_DB_PATH` | No | `data/inspectai.db` | SQLite database path |
| `INSPECTAI_LOG_LEVEL` | No | `INFO` | Logging verbosity |

## Security Considerations

1. **API Key Protection** — Never commit `.env` to version control. Use environment variables or a secrets manager.
2. **HTTPS** — Always use HTTPS in production. Use a reverse proxy (nginx, Caddy) with Let's Encrypt.
3. **File Upload Limits** — The app enforces 15MB per image. Adjust `MAX_FILE_SIZE_MB` if needed.
4. **CORS** — If exposing an API layer, configure CORS policies.
5. **Database Backups** — Regularly backup the SQLite database. Consider automated daily backups.

## Monitoring

```bash
# Check app health
curl -f http://localhost:8501/_stcore/health

# Check logs
journalctl -u inspectai -f  # systemd
docker logs inspectai      # Docker
```

## Scaling

For production deployments with multiple concurrent users:

| Approach | When to Use |
|----------|-------------|
| Single instance + nginx | <50 concurrent users |
| Docker Compose (multiple replicas) | 50–200 concurrent users |
| Kubernetes + HPA | 200+ concurrent users |
| Separate API layer (FastAPI) | When Streamlit's single-threaded model becomes a bottleneck |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is activated; run `pip install -r requirements.txt` |
| Gemini API errors | Verify `GEMINI_API_KEY` is set correctly; check API quota |
| OpenCV import errors | Install `libgl1` and `libglib2.0-0` system packages |
| Database locked | SQLite doesn't handle concurrent writes well; use WAL mode or PostgreSQL |
| Memory errors | Reduce `max_dimension` in `image_optimizer.py`; limit batch size |
| Port already in use | Change `--server.port` or stop the conflicting process |
