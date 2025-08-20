# DollarPunk - Ingestion Module

Questo modulo si occupa dell'ingestione di dati finanziari tramite l'API Alpha Vantage.

## Struttura

- `ingest.py` - Script principale per l'ingestione dei dati
- `requirements.txt` - Dipendenze Python
- `Dockerfile` - Configurazione Docker
- `docker-compose.yml` - Orchestrazione Docker locale

## Configurazione

Il sistema utilizza due file di configurazione:

### 1. File `.env` (per le chiavi API)
Crea un file `.env` nella directory `ingestion/` con:
```
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

### 2. File `.conf` (per i parametri di configurazione)
Il file `.conf` è già configurato con i parametri necessari:
- `TICKERS`: Lista dei ticker da monitorare
- `MAX_TICKERS_PER_RUN`: Numero massimo di ticker per esecuzione
- `DAYS_TO_FETCH`: Giorni di dati storici da recuperare

Per maggiori dettagli sulla configurazione, consulta [CONFIGURATION.md](CONFIGURATION.md).

### 3. Directory Output
Assicurati che esista la cartella `output/` nella root del progetto

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
