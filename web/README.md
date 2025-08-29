# DollarPunk - Software Portafoglio

Applicazione web per la gestione del portafoglio investimenti con dati reali da Alpha Vantage API.

## Caratteristiche

- 📊 Dashboard con dati reali del portafoglio
- 📈 Prezzi in tempo reale da Alpha Vantage
- 💰 Calcolo automatico di guadagni/perdite
- 📋 Gestione posizioni e ordini
- 📊 Report e analisi

## Configurazione

### 1. Installazione dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configurazione API Key

1. Ottieni una API key gratuita su [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Crea un file `.env` nella **root del progetto** (cartella principale DollarPunk):
```bash
# Dalla root del progetto
cp web/env.example .env
```
3. Inserisci la tua API key nel file `.env`:
```
ALPHA_VANTAGE_API_KEY=your_actual_api_key_here
```

### 3. Avvio applicazione

#### Opzione 1: Avvio diretto
```bash
python app.py
```

#### Opzione 2: Con Docker
```bash
# Build e avvio con docker-compose (dalla cartella web/)
cd web
docker-compose up --build

# Oppure solo con Docker
docker build -t dollarpunk .
docker run -p 5000:5000 --env-file ../.env dollarpunk
```

L'applicazione sarà disponibile su: http://localhost:5000

## Portafoglio di Esempio

L'applicazione include un portafoglio di esempio con i seguenti titoli:
- AAPL (Apple)
- MSFT (Microsoft)
- NVDA (NVIDIA)
- TSLA (Tesla)
- ENEL.MI (Enel)
- GOOGL (Alphabet)
- AMZN (Amazon)
- META (Meta)

## API Endpoints

- `GET /api/portfolio` - Dati completi del portafoglio
- `GET /api/stock/<symbol>` - Dati di un singolo titolo
- `GET /api/search?q=<query>` - Ricerca titoli

## Limitazioni Alpha Vantage

- **Free Tier**: 5 chiamate API al minuto
- **Rate Limiting**: L'applicazione include un delay di 0.2 secondi tra le chiamate
- **Simboli**: Supporta simboli NASDAQ, NYSE e alcuni mercati europei

## Struttura Progetto

```
DollarPunk/
├── .env               # API Key (da creare)
├── web/
│   ├── app.py              # Server Flask
│   ├── requirements.txt    # Dipendenze Python
│   ├── env.example        # Esempio configurazione
│   ├── templates/         # Template HTML
│   │   └── portfolio-software.html
│   ├── docker-compose.yml # Docker compose
│   ├── Dockerfile        # Docker image
│   └── README.md         # Questo file
└── ... (altri file del progetto)
```

## Sviluppo

Per modificare il portafoglio di esempio, edita la variabile `SAMPLE_PORTFOLIO` in `app.py`.

Per aggiungere nuove funzionalità, puoi:
1. Aggiungere nuovi endpoint API in `app.py`
2. Modificare l'interfaccia in `templates/portfolio-software.html`
3. Aggiungere nuove sezioni e funzionalità JavaScript
