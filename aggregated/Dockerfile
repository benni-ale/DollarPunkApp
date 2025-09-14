FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY aggregate.py .
COPY main.py .

# Create data directories
RUN mkdir -p /app/data/input /app/data/output/aggregated

# Set the default command
CMD ["python", "main.py"]
