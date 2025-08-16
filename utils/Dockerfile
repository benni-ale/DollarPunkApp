FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all utils files
COPY . .

# Set the default command to run the extract_tickers_cmp.py script
CMD ["python", "extract_tickers_cmp.py"]
