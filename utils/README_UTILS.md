# DollarPunk Utils Module

This module contains utility scripts for the DollarPunk project, including the `extract_tickers_cmp.py` script for extracting US stock tickers from market cap data.

## Scripts

### extract_tickers_cmp.py
Extracts US stock tickers from CompaniesMarketCap.com data. The script:
- Reads HTML data from `snippet.html`
- Parses the market cap table
- Filters for US companies only
- Extracts ticker symbols
- Outputs the list of tickers

## Containerization

The utils folder is fully containerized for easy execution.

### Running with Docker Compose

From the project root:
```bash
docker-compose up dollarpunk-utils
```

From the utils directory:
```bash
cd utils
docker-compose up --build
```

### Running with Docker directly

```bash
cd utils
docker build -t dollarpunk-utils .
docker run --rm -v $(pwd):/app dollarpunk-utils
```

### Running the shell script

```bash
cd utils
chmod +x run.sh
./run.sh
```

## Dependencies

- Python 3.11
- beautifulsoup4
- requests
- lxml

## Output

The script outputs a list of US stock tickers to the console. You can modify the script to save the output to a file by uncommenting the CSV export section.

## Files

- `extract_tickers_cmp.py` - Main script
- `snippet.html` - HTML data source
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Local orchestration
- `run.sh` - Convenience script
