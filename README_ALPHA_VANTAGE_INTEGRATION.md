# Alpha Vantage Integration con Database MySQL

Questo documento descrive come utilizzare l'integrazione Alpha Vantage per raccogliere dati finanziari reali e salvarli in modo idempotente nel database MySQL.

## 🚀 Setup Rapido

### 1. Configurazione API Key

1. Ottieni una API key gratuita da [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Crea un file `.env` nella root del progetto con le seguenti variabili:

```bash
# Configurazione Database MySQL
DATABASE=mysql://benni_ale:Luisa47-@localhost/dollarpunk

# API Key Alpha Vantage
ALPHA_VANTAGE_API_KEY=your_real_api_key_here
```

**Alternativa**: Puoi specificare l'API key via parametro CLI:
```bash
cargo run -- test-alpha-vantage --api-key "your_api_key_here"
```

### 2. Setup Database MySQL

Assicurati che MySQL sia in esecuzione e crea il database:

```sql
CREATE DATABASE dollarpunk;
```

### 3. Test dell'Integrazione

Esegui lo script di test:

```bash
chmod +x test_alpha_vantage.sh
./test_alpha_vantage.sh
```

## 📊 Comandi CLI

### Test Alpha Vantage (senza database)

```bash
# Usa API key dal file .env
cargo run -- test-alpha-vantage --config config_alpha_vantage.toml

# Oppure specifica API key via parametro
cargo run -- test-alpha-vantage --config config_alpha_vantage.toml --api-key "your_api_key"
```

### Test Alpha Vantage con database

```bash
# Usa configurazioni dal file .env
cargo run -- test-alpha-vantage --config config_alpha_vantage.toml --save-to-db

# Oppure specifica tutto via parametri
cargo run -- test-alpha-vantage \
    --config config_alpha_vantage.toml \
    --api-key "your_api_key" \
    --database-url "mysql://username:password@localhost/dollarpunk" \
    --save-to-db
```

### Raccolta dati completa con database

```bash
cargo run -- collect-data \
    --config config_alpha_vantage.toml \
    --database-url "mysql://root:password@localhost/dollarpunk" \
    --save-to-db
```

## 🔧 Configurazione Dettagliata

### File di Configurazione

Il file `config_alpha_vantage.toml` contiene:

- **Modalità**: `prod` per dati reali, `demo` per dati simulati
- **API Key**: Chiave per l'accesso all'API Alpha Vantage
- **Keywords**: Termini di ricerca per filtrare le notizie
- **Filtri**: Lingue, engagement minimo, esclusione retweet/ads

### Struttura Database

Il sistema crea automaticamente le seguenti tabelle:

#### `data_points`
- `id`: Identificatore univoco del punto dati
- `content`: Contenuto della notizia
- `platform`: Piattaforma di origine (AlphaVantage)
- `timestamp`: Data e ora della notizia
- `theme`: Tema categorizzato (Economy, Technology, etc.)
- `author`: Autore della notizia
- `url`: Link alla notizia originale
- `engagement_*`: Metriche di engagement (simulate per Alpha Vantage)
- `language`: Lingua del contenuto
- `sentiment_score`: Punteggio di sentiment da Alpha Vantage

#### `collection_sessions`
- Traccia le sessioni di raccolta dati
- Stato: running, completed, failed, cancelled

#### `alpha_vantage_queries`
- Log delle query API effettuate
- Statistiche di successo/fallimento

## 🔄 Inserimento Idempotente

Il sistema garantisce l'inserimento idempotente dei dati:

1. **Identificazione Univoca**: Ogni punto dati ha un ID univoco basato su contenuto e timestamp
2. **Upsert**: Utilizza `INSERT ... ON DUPLICATE KEY UPDATE` per evitare duplicati
3. **Aggiornamento**: Se un record esiste già, viene aggiornato con i nuovi dati
4. **Tracciabilità**: Ogni operazione è tracciata nelle tabelle di log

## 📈 Dati Alpha Vantage

### Endpoint Utilizzati

- **NEWS_SENTIMENT**: Notizie finanziarie con analisi del sentiment
- **Limit**: Fino a 50 notizie per richiesta
- **Topics**: Filtro per argomenti specifici
- **Time Range**: Ultimi 7 giorni

### Struttura Dati

Ogni notizia Alpha Vantage include:

- **Titolo e Riepilogo**: Contenuto principale
- **Autori**: Lista degli autori
- **Fonte**: Testata giornalistica
- **Categoria**: Categoria della notizia
- **Sentiment Score**: Punteggio di sentiment (-1.0 a +1.0)
- **Ticker Sentiment**: Sentiment per specifici ticker azionari
- **Topics**: Argomenti correlati

### Categorizzazione Automatica

Il sistema categorizza automaticamente le notizie in:

- **Economy**: Finanza, mercati, inflazione, Fed
- **Technology**: Tech, AI, software
- **Politics**: Politica, governo
- **Other**: Altri argomenti

## 🛠️ Risoluzione Problemi

### Errori Comuni

#### API Key Non Valida
```
❌ Alpha Vantage API error: Invalid API call
```
**Soluzione**: Verifica che l'API key sia corretta e abbia crediti sufficienti

#### Rate Limit
```
⚠️ Alpha Vantage API note: Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day.
```
**Soluzione**: Rispetta i limiti di frequenza delle chiamate API

#### Database Connection Error
```
❌ Errore nella connessione al database
```
**Soluzione**: 
1. Verifica che MySQL sia in esecuzione
2. Controlla l'URL di connessione
3. Assicurati che il database esista

### Modalità Demo

Se non hai un'API key valida, puoi testare con dati simulati:

```bash
cargo run -- test-alpha-vantage --config config_alpha_vantage.toml --demo
```

## 📊 Monitoraggio e Statistiche

### Statistiche Database

Il sistema fornisce statistiche in tempo reale:

- **Totale punti dati**: Numero totale di record
- **Punti oggi**: Record inseriti oggi
- **Sentiment medio**: Sentiment medio di tutti i dati
- **Distribuzione per piattaforma**: Conteggi per piattaforma

### Log delle Query

Ogni query Alpha Vantage è registrata con:

- Timestamp della query
- Argomenti di ricerca
- Numero di risultati
- Stato (success/failed/partial)
- Messaggi di errore

## 🔮 Prossimi Sviluppi

- [ ] Supporto per altri endpoint Alpha Vantage (TIME_SERIES, FOREX, etc.)
- [ ] Analisi avanzata del sentiment per ticker specifici
- [ ] Dashboard web per visualizzare i dati
- [ ] Alert automatici per notizie importanti
- [ ] Integrazione con altri provider di dati finanziari

## 📞 Supporto

Per problemi o domande:

1. Controlla i log dell'applicazione
2. Verifica la configurazione del database
3. Testa l'API key Alpha Vantage separatamente
4. Consulta la documentazione Alpha Vantage per limiti e endpoint 