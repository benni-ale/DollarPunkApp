# 📈 Schede Titoli - DollarPunk

Un'applicazione web per visualizzare informazioni dettagliate sui titoli azionari utilizzando l'API di Alpha Vantage.

## 🚀 Come Funziona

1. **Backend** (porta 8000): API FastAPI che recupera dati da Alpha Vantage
2. **Frontend** (porta 3000): Interfaccia web React per visualizzare le schede dei titoli

## 📋 Prerequisiti

- Docker e Docker Compose installati
- Chiave API Alpha Vantage nel file `.env` della root del progetto

## 🛠️ Setup

1. **Assicurati di avere il file `.env` nella root del progetto:**
   ```
   ALPHAVANTAGE_API_KEY=la_tua_chiave_api_qui
   ```

2. **Avvia l'applicazione:**
   ```bash
   cd armando/schede_titoli
   docker-compose up --build
   ```

3. **Apri il browser su:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## 🎯 Come Usare l'Applicazione

### Visualizzazione Titoli
- L'app mostra automaticamente AAPL, MSFT e GOOGL all'avvio
- Usa la barra di ricerca per aggiungere nuovi titoli
- Clicca ❌ per rimuovere un titolo dalla vista

### Informazioni Mostrate
Per ogni titolo vedrai:
- **Prezzo attuale** e variazione percentuale
- **Dati fondamentali**: Settore, Capitalizzazione, P/E, Beta, Dividend Yield
- **Grafico** dell'andamento del prezzo negli ultimi 200 giorni
- **Dettagli**: Nome azienda, valuta, data ultimo aggiornamento

### Esempi di Simboli
- **USA**: AAPL, MSFT, GOOGL, TSLA, AMZN, META
- **Italia**: ENI.MI, ENEL.MI, TIT.MI, ISP.MI
- **Altri**: ASML, NVDA, BRK.A

## 🔧 API Endpoints

- `GET /api/stock/{symbol}` - Dati completi per un simbolo
  - Esempio: `http://localhost:8000/api/stock/AAPL`

## 🎨 Caratteristiche

- **Cache intelligente**: Dati in cache per 60 secondi
- **Gestione errori**: Rate limit e problemi API gestiti automaticamente
- **CORS abilitato**: Frontend e backend comunicano senza problemi
- **Design responsive**: Funziona su desktop e mobile
- **Hot reload**: Sviluppo facilitato con auto-ricaricamento

## 🐛 Risoluzione Problemi

### Errore "Rate limit"
- L'API Alpha Vantage ha limiti di utilizzo
- Aspetta qualche minuto e riprova

### Titolo non trovato
- Verifica che il simbolo sia corretto
- Alcuni titoli potrebbero non essere disponibili

### Problemi di connessione
- Verifica che entrambi i servizi (backend e frontend) siano in esecuzione
- Controlla i log con `docker-compose logs`

## 📁 Struttura Progetto

```
armando/schede_titoli/
├── backend/
│   ├── backend.py          # API FastAPI
│   ├── requirements.txt    # Dipendenze Python
│   └── Dockerfile         # Container backend
├── frontend/
│   ├── index.html         # Interfaccia web
│   ├── server.py          # Server frontend
│   └── Dockerfile         # Container frontend
├── docker-compose.yml     # Orchestrazione servizi
└── README.md             # Questa documentazione
```

## 🔄 Sviluppo

Per modificare il codice:
1. Modifica i file nella directory appropriata
2. I container si ricaricano automaticamente grazie al volume mounting
3. Le modifiche sono visibili immediatamente

## 📊 Dati Disponibili

L'API fornisce:
- **Quote in tempo reale**: Prezzo, variazione, volume
- **Dati fondamentali**: Settore, capitalizzazione, metriche finanziarie
- **Serie storiche**: Andamento prezzo ultimi 200 giorni
- **Informazioni aziendali**: Nome, valuta, settore
