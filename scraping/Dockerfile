FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the scraping scripts
COPY scrape.py .
COPY scrape_coordinator.py .

# Create output directory
RUN mkdir -p /app/output

CMD ["python", "scrape.py"]
