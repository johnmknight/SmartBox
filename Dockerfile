FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/photos /app/client/assets

# Expose internal port
EXPOSE 8091

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8091"]
