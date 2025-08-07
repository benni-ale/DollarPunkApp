# DollarPunk News Ingest

Containerized application to fetch news sentiment data from Alpha Vantage API.

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

### Using Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Using Docker directly
```bash
# Build the image
docker build -t dollarpunk-ingest .

# Run the container
docker run --env-file .env -v $(pwd)/output:/app/output dollarpunk-ingest
```

## Output

The application will create `output/news_data.json` with the fetched news sentiment data.

## Environment Variables

- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key (required)
- `TICKERS`: Comma-separated list of stock tickers to fetch news for (default: AAPL,TSLA,MSFT,GOOGL,NVDA,AMZN) 