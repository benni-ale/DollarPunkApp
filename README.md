# DollarPunk News Ingest

Simple containerized application to fetch news sentiment data from Alpha Vantage API.

## Setup

1. Create a `.env` file in the root directory with your Alpha Vantage API key:
```
ALPHA_VANTAGE_API_KEY=your_api_key_here
TICKERS=AAPL,TSLA,MSFT,GOOGL,NVDA,AMZN
```

2. Create the output directory:
```bash
mkdir output
```

## Usage

### Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

### Run with Docker directly

```bash
# Build the image
docker build -t dollarpunk-ingest .

# Run the container
docker run --env-file .env -v $(pwd)/output:/app/output dollarpunk-ingest
```

### Run locally

```bash
pip install -r requirements.txt
python ingest.py
```

## Output

The application creates timestamped files in the `output/` directory with the format:
- `news_data_YYYYMMDD_HHMMSS.json` (e.g., `news_data_20250115_143022.json`)

Each run creates a new file with the current timestamp.

## Environment Variables

- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key (required)
- `TICKERS`: Comma-separated list of stock tickers to fetch news for (default: AAPL,TSLA,MSFT,GOOGL,NVDA,AMZN) 