# Stocks Data Fetcher

Containerized service to fetch historical stock price data from Alpha Vantage API and save it as CSV files.

## Prerequisites

- Docker and Docker Compose installed
- Alpha Vantage API key in the `.env` file
- Tickers list configured in the `.env` file

## Environment Variables

Create a `.env` file in the root directory with:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
TICKERS=AAPL,MSFT,GOOGL,TSLA,AMZN
MAX_TICKERS_PER_RUN=10
DAYS_TO_FETCH=365
SLEEP_BETWEEN_CALLS=15
MAX_RETRIES=3
```

## Usage

### Build and run the container:

```bash
# From the stocks directory
docker-compose up --build

# Or from the root directory
docker-compose -f stocks/docker-compose.yml up --build
```

### Run with custom parameters:

```bash
# Override environment variables
TICKERS=AAPL,MSFT docker-compose up --build

# Or modify the docker-compose.yml file to uncomment the environment section
```

## Output

CSV files will be saved to `../output/stocks/` directory with the following format:
- `SYMBOL.csv` (e.g., `AAPL.csv`, `MSFT.csv`)

Each CSV contains:
- `date`: Date in YYYY-MM-DD format
- `open`: Opening price
- `high`: Highest price of the day
- `low`: Lowest price of the day
- `close`: Closing price
- `volume`: Trading volume

## Features

- **Rate limiting**: Respects Alpha Vantage API limits (5 requests/minute for free tier)
- **Incremental updates**: Only fetches new data, skips existing dates
- **Error handling**: Retries on rate limits, skips invalid symbols
- **Progress tracking**: Shows progress with tqdm
- **Flexible configuration**: All parameters configurable via environment variables

## Notes

- The free Alpha Vantage API has a limit of 5 requests per minute
- The script automatically handles rate limiting with exponential backoff
- CSV files are appended to, so you can run the script multiple times safely
