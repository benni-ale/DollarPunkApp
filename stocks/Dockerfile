FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script
COPY fetch.py .

# Create output directory
RUN mkdir -p /app/output/stocks

# Set volume for output folder
VOLUME ["/app/output"]
# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "fetch.py"]
