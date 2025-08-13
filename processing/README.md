# News Data Processor

Script per processare i dati delle news JSON e creare tabelle separate per topics e tickers.

## Funzionalità

- **Deduplicazione**: Rimuove duplicati basandosi sull'URL, mantenendo il record più recente
- **Separazione dati**: Crea due tabelle distinte:
  - `topics.csv`: Esplode l'array `topics` con tutti i metadati della news
  - `tickers.csv`: Esplode l'array `ticker_sentiment` con tutti i metadati della news
- **Full overwrite**: Salva sia versioni con timestamp che versioni per overwrite

## Struttura Output

### Tabella Topics
- `url`: URL della news
- `title`: Titolo della news
- `summary`: Riassunto della news
- `authors`: Array degli autori (JSON string)
- `time_published`: Data di pubblicazione
- `source`: Fonte della news
- `source_domain`: Dominio della fonte
- `category_within_source`: Categoria nella fonte
- `banner_image`: URL dell'immagine banner
- `overall_sentiment_score`: Score del sentiment generale
- `overall_sentiment_label`: Label del sentiment generale
- `source_ticker`: Ticker di origine
- `ingestion_timestamp`: Timestamp di ingestione
- `topic`: Topic specifico
- `relevance_score`: Score di rilevanza del topic

### Tabella Tickers
- Tutti i metadati della news (come sopra)
- `ticker`: Simbolo del ticker
- `relevance_score`: Score di rilevanza del ticker
- `ticker_sentiment_score`: Score del sentiment del ticker
- `ticker_sentiment_label`: Label del sentiment del ticker

## Installazione e Utilizzo

### Docker (Raccomandato)

```bash
cd processing
docker-compose up --build
```

### Locale (Alternativa)

```bash
cd processing
pip install -r requirements.txt
python process_news_data.py
```

## Output

Lo script crea i seguenti file nella directory `../output/processed/`:

### Tabelle CSV
- `topics.csv`: Tabella topics (overwrite)
- `tickers.csv`: Tabella tickers (overwrite)

### Delta Logging
Il sistema di delta logging monitora le modifiche tra le esecuzioni:

#### Directory `delta_log/`
- `topics_delta_YYYYMMDD_HHMMSS.json`: Log delle modifiche per topics
- `tickers_delta_YYYYMMDD_HHMMSS.json`: Log delle modifiche per tickers
- `topics_previous_hashes.txt`: Hash dello stato precedente topics
- `tickers_previous_hashes.txt`: Hash dello stato precedente tickers

#### Chiavi Delta Log
- **Topics**: `URL + topic` (es: `https://example.com|Technology`)
- **Tickers**: `URL + ticker` (es: `https://example.com|MSFT`)

#### Struttura Delta Log
```json
{
  "timestamp": "20250813_124318",
  "table_name": "topics",
  "insertions_count": 150,
  "deletions_count": 25,
  "insertions": ["abc123...", "def456..."],  // Hash dei record aggiunti
  "deletions": ["ghi789...", "jkl012..."]    // Hash dei record rimossi
}
```

## Logging

Lo script fornisce log dettagliati durante l'elaborazione, inclusi:
- Numero di file JSON processati
- Record caricati e deduplicati
- Statistiche finali sui dati elaborati

## Struttura Directory

```
processing/
├── Dockerfile              # Configurazione Docker
├── docker-compose.yml      # Orchestrazione Docker
├── process_news_data.py    # Script principale
├── reorganize_files.py     # Script per riorganizzare i file
├── requirements.txt        # Dipendenze Python
├── README.md              # Documentazione
└── .dockerignore          # File da escludere dal build

../output/                 # Directory principale
├── ingested/              # File JSON delle news (input)
└── processed/             # Tabelle CSV e delta log (output)
```

## Workflow Completo

### 1. Ingestion (Genera nuovi file)
```bash
cd ingestion
docker-compose up --build
```
- Scrive file JSON in `../output/ingested/` con formato: `news_data_batch_20250808_100548_0001.json`

### 2. Riorganizzazione (Solo per file esistenti)
Se hai file vecchi da riorganizzare:
```bash
cd processing
python reorganize_files.py
```
- Sposta file dalla directory principale a `../output/ingested/`
- Rinomina: `news_data_batch_0001_20250808_100548.json` → `news_data_batch_20250808_100548_0001.json`

### 3. Processing
```bash
cd processing
docker-compose up --build
```
- Legge da `../output/ingested/`
- Scrive tabelle in `../output/processed/`

## Volumi Docker

Il container Docker monta il seguente volume:
- `../output:/app/output` - Directory principale (lettura/scrittura)
  - `/app/output/ingested/` - File JSON di input (lettura)
  - `/app/output/processed/` - Tabelle CSV e delta log di output (scrittura)
