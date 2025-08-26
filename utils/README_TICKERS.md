# Tickers Extractor Container

Questo container scarica il listing status completo da Alpha Vantage e estrae tutti i symbol e name.

## Funzionalità

- Scarica il file completo di listing status da Alpha Vantage
- Estrae solo symbol e name per ogni ticker
- Salva i risultati in formato JSON e CSV con timestamp
- Output semplificato e pulito

## Prerequisiti

Assicurati di avere la chiave API di Alpha Vantage nel file `.env`:
```
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## Utilizzo

### Build e run del container

```bash
# Dalla directory utils/
docker-compose up --build
```

### Run manuale

```bash
# Build dell'immagine
docker build -t dollarpunk-tickers .

# Run del container
docker run -v $(pwd)/../output:/app/output -v $(pwd)/../.env:/app/.env:ro dollarpunk-tickers
```

## Output

Il container genera quattro file:

1. **`listing_status_YYYYMMDD_HHMMSS.csv`** - File completo di Alpha Vantage
2. **`tickers_YYYYMMDD_HHMMSS.json`** - Ticker in formato JSON
3. **`tickers_YYYYMMDD_HHMMSS.csv`** - Ticker in formato CSV (symbol + name)
4. **`symbols_YYYYMMDD_HHMMSS.csv`** - Solo simboli in formato CSV

### Formato JSON

```json
{
  "timestamp": "20241201_143022",
  "source": "Alpha Vantage Listing Status",
  "total_tickers": 15000,
  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc"
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft Corporation"
    }
  ]
}
```

### Formato CSV (tickers)

```csv
symbol,name
AAPL,Apple Inc
MSFT,Microsoft Corporation
GOOGL,Alphabet Inc
```

### Formato CSV (symbols only)

```csv
symbol
AAPL
MSFT
GOOGL
TSLA
NVDA
```

## Vantaggi

- **Output semplificato**: Solo symbol e name
- **Formato flessibile**: JSON per analisi, CSV per Excel
- **Tracciabilità**: Timestamp per ogni esecuzione
- **Completo**: Include tutti i ticker disponibili su Alpha Vantage
