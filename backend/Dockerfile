FROM python:3.12-slim

# Install build dependencies for pyswisseph and git
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ git && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set up user and home directory for HF Spaces (required to run under user 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

# Copy dependency files first (for Docker layer caching)
COPY --chown=user pyproject.toml uv.lock .python-version ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=user . .

# HF Spaces default port
EXPOSE 7860

# Write GCP_CREDENTIALS_JSON to a file at runtime, then start the application.
CMD sh -c 'if [ -n "$GCP_CREDENTIALS_JSON" ]; then python -c "import os; open(\"/home/user/app/gcp.json\", \"w\").write(os.environ[\"GCP_CREDENTIALS_JSON\"])" && export GOOGLE_APPLICATION_CREDENTIALS=/home/user/app/gcp.json && export GCP_CREDENTIALS_PATH=/home/user/app/gcp.json; fi && exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}" --workers 2'
