# DollarPunk News Ingester

A Python application for ingesting financial news data from Alpha Vantage API and storing it in JSON format.

## Features

- Fetches news sentiment data for specified stock tickers
- Supports both real-time and historical news ingestion
- Intelligent batching and duplicate detection
- Docker containerization for easy deployment
- Configurable rate limiting and retry logic

## Recent Fixes (August 2025)

### API Error Handling
- Enhanced error detection for Alpha Vantage API responses
- Added handling for "Information", "Error Message", and "Note" keys
- Implemented automatic fallback to non-date-filtered requests when date filters fail
- Added intelligent rate limit detection with appropriate delays

### Rate Limiting Improvements
- Implemented 30-day date chunking to avoid overwhelming the API
- Added configurable delays: 45 seconds between chunks, 90 seconds between tickers
- Introduced `MAX_TICKERS_PER_RUN` to limit concurrent ticker processing (default: 3)
- Added retry logic with `MAX_RETRIES` for failed API calls

### Historical Data Processing
- Broke down 365-day historical ingestion into manageable chunks
- Added API connection testing before starting ingestion
- Improved progress tracking and error reporting
- Enhanced metadata tracking for historical fetches

## Configuration

Create a `.env` file in the project root with:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
TICKERS=AAPL,TSLA,MSFT,GOOG,NVDA,AMZN
MAX_TICKERS_PER_RUN=3
BATCH_SIZE=100
MAX_RUNTIME_HOURS=8
SLEEP_BETWEEN_RUNS=300
```

## Usage

### Docker Compose (Recommended)

```bash
docker-compose up
```

### Direct Python

```bash
pip install -r requirements.txt
python ingest.py
```

## Ingestion Modes

- **Mode 1**: Real-time news ingestion
- **Mode 2**: Historical news ingestion (last 365 days)

## Output

News data is stored in the `output/` directory with:
- Individual batch files for large datasets
- Duplicate detection and prevention
- Comprehensive metadata tracking
- JSON format for easy processing

## API Considerations

- Alpha Vantage has rate limits that are automatically handled
- Historical ingestion is chunked to respect API constraints
- Automatic retry logic for failed requests
- Fallback mechanisms for date-filtered queries 