# DollarPunk

Un'applicazione modulare per l'analisi di dati finanziari, composta da moduli di ingestione e processing.

## Struttura del Progetto

```
DollarPunk/
├── ingestion/          # Modulo di ingestione dati
│   ├── ingest.py       # Script principale ingestione
│   ├── requirements.txt # Dipendenze Python
│   ├── Dockerfile      # Configurazione Docker
│   ├── docker-compose.yml # Orchestrazione locale
│   └── README.md       # Documentazione modulo
├── output/             # Dati ingeriti (condivisi)
├── docker-compose.yml  # Orchestrazione principale
└── README.md          # Questo file
```

## Moduli

### 🚀 Ingestion Module (`ingestion/`)

Modulo per l'ingestione di dati finanziari tramite Alpha Vantage API.

**Features:**
- Fetch di news sentiment per ticker specificati
- Supporto per dati real-time e storici (ultimi 365 giorni)
- Batching intelligente e rilevamento duplicati
- Containerizzazione Docker per deployment semplice
- Rate limiting configurabile e logica di retry

**Configurazione:**
Crea un file `.env` nella root del progetto:
```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
TICKERS=AAPL,TSLA,MSFT,GOOG,NVDA,AMZN
MAX_TICKERS_PER_RUN=3
```

**Esecuzione:**
```bash
# Docker (raccomandato)
docker-compose up

# Locale
cd ingestion
pip install -r requirements.txt
python ingest.py
```

**Modalità:**
- **Mode 1**: Real-time news ingestion (8 ore)
- **Mode 2**: Historical news ingestion (ultimi 365 giorni) - Default

### 🔄 Processing Module (Coming Soon)

Modulo per l'elaborazione e analisi dei dati ingeriti.

## Output

I dati vengono salvati in `output/` con:
- File batch individuali per dataset grandi
- Rilevamento e prevenzione duplicati
- Tracking metadata completo
- Formato JSON per facile elaborazione

## Considerazioni API

- Alpha Vantage ha rate limits gestiti automaticamente
- L'ingestione storica è chunked per rispettare i vincoli API
- Logica di retry automatica per richieste fallite
- Meccanismi di fallback per query con filtri temporali

## Sviluppo

Per aggiungere nuovi moduli:
1. Crea una nuova cartella per il modulo
2. Aggiungi i file necessari (Dockerfile, requirements.txt, etc.)
3. Aggiorna questo README con la documentazione del modulo
4. Considera l'integrazione con `docker-compose.yml` principale 