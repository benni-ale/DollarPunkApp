FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY tickers.py .

# Create output directory
RUN mkdir -p /app/output

# Set volume for output folder
VOLUME ["/app/output"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the script
CMD ["python", "tickers.py"]
