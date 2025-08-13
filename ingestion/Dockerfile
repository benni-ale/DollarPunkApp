FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the ingestion script
COPY ingest.py .

# Create output directory
RUN mkdir -p /app/output

# Set volume for output folder
VOLUME ["/app/output"]

# Set default mode (can be overridden)
ENV INGESTION_MODE=2

# Run the ingestion directly
CMD ["python", "ingest.py"] 