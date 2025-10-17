FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including docker CLI and docker-compose
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    docker-compose \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install huggingface-cli for model downloads
RUN pip install --no-cache-dir huggingface-hub[cli]

# Copy application code
COPY . .

# Expose port
EXPOSE 8787

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8787"]
