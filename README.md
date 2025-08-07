# DollarPunk News Ingest

Containerized application to fetch news sentiment data from Alpha Vantage API with interactive monitoring dashboard.

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

### Interactive Dashboard (Recommended)

Start the unified application:

```bash
docker-compose up --build
```

Then open your browser and go to: **http://localhost:5000**

The dashboard provides:
- 📊 Real-time statistics
- 📈 Interactive charts (articles per ticker, sentiment distribution)
- 🎮 Start/Stop controls for ingestion
- 📰 Latest articles preview
- 📋 Live logs
- ⚡ Auto-refresh every 5 seconds

### Single Command
Just run `docker-compose up --build` and everything is ready!

### Using Docker directly
```bash
# Build the image
docker build -t dollarpunk-ingest .

# Run the container
docker run --env-file .env -v $(pwd)/output:/app/output dollarpunk-ingest
```

## Dashboard Features

- **Real-time Monitoring**: Live updates of ingestion progress
- **Interactive Charts**: Visual representation of data distribution
- **Control Panel**: Start/stop ingestion with one click
- **Live Logs**: Monitor Docker container logs in real-time
- **Statistics**: Total articles, sentiment analysis, ticker breakdown
- **Latest Articles**: Preview of most recent news articles

## Output

The application will create `output/news_data.json` with the fetched news sentiment data.

## Environment Variables

- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key (required)
- `TICKERS`: Comma-separated list of stock tickers to fetch news for (default: AAPL,TSLA,MSFT,GOOGL,NVDA,AMZN) 