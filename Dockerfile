FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 planos && chown -R planos:planos /app
USER planos

EXPOSE 8000

CMD ["uvicorn", "planos.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
