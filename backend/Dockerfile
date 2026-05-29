FROM python:3.12-slim

# Install build dependencies for pyswisseph
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml .
COPY .python-version .

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY . .

# HF Spaces default port
EXPOSE 7860

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "2"]
