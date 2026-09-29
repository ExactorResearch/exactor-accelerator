# Dockerfile for Exactor Accelerator microservice deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml README.md ./
COPY exactor_accelerator ./exactor_accelerator

# Install library with server extra
RUN pip install --no-cache-dir .[server]

# Environment variable for model file
ENV MODEL_PATH=/app/model.ea
ENV PORT=8000

EXPOSE 8000

# Entrypoint for model server
CMD ["sh", "-c", "python -m exactor_accelerator.model_server --model ${MODEL_PATH} --host 0.0.0.0 --port ${PORT}"]
