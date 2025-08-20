FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and config file
COPY reddit_ingestion.py .
COPY .conf .

# Create output and logs directories
RUN mkdir -p /app/output /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "reddit_ingestion.py"]

