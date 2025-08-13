# DollarPunk - Ingestion Module

Questo modulo si occupa dell'ingestione di dati finanziari tramite l'API Alpha Vantage.

## Struttura

- `ingest.py` - Script principale per l'ingestione dei dati
- `requirements.txt` - Dipendenze Python
- `Dockerfile` - Configurazione Docker
- `docker-compose.yml` - Orchestrazione Docker locale

## Configurazione

1. Crea un file `.env` nella root del progetto con:
   ```
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   TICKERS=AAPL,MSFT,GOOGL,AMZN,TSLA
   MAX_TICKERS_PER_RUN=3
   ```

2. Assicurati che esista la cartella `output/` nella root del progetto

## Modalità di Esecuzione

### Modalità 1: Continuous Ingestion (8 ore)
```bash
docker-compose up --build
```

### Modalità 2: Historical Year Ingestion (ultimi 365 giorni)
```bash
docker-compose up --build
```
(Default mode)

### Modalità 3: Esecuzione Locale
```bash
cd ingestion
pip install -r requirements.txt
python ingest.py
```

## Output

I dati vengono salvati in `../output/` con il formato:
- `news_data_batch_XXXX_YYYYMMDD_HHMMSS.json`

Ogni batch contiene fino a 100 articoli e include metadata come:
- `source_ticker`: Il ticker che ha generato l'articolo
- `ingestion_timestamp`: Timestamp dell'ingestione
- `historical_fetch`: Flag per dati storici
- `fetch_date_range`: Range di date per i dati storici
