FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the join script
COPY join.py .

# Create output directory
RUN mkdir -p /app/output

# Set the default command
CMD ["python", "join.py"]
