FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ingest.py .

# Create output directory
RUN mkdir -p /app/output

# Set volume for output folder
VOLUME ["/app/output"]

# Run the application
CMD ["python", "ingest.py"] 