# DollarPunk - Integrazione Alpha Vantage

## 🚀 Panoramica

DollarPunk ora supporta l'integrazione con **Alpha Vantage**, un'API che fornisce news finanziarie con sentiment analysis già integrata. Questa integrazione permette di raccogliere dati finanziari di alta qualità con punteggi di sentiment pre-calcolati.

## ✨ Vantaggi dell'Integrazione

### 📊 Sentiment Analysis Pre-calcolata
- **Punteggi accurati**: Utilizza algoritmi avanzati di NLP
- **Risparmio di risorse**: Non serve implementare analisi locale
- **Consistenza**: Metodologia uniforme per tutti i punteggi

### 📈 Dati Finanziari Specializzati
- **News curate**: Contenuti specifici per il mercato finanziario
- **Categorizzazione automatica**: Classificazione per argomenti e settori
- **Analisi per ticker**: Sentiment specifico per singole azioni/crypto

### 🔍 Qualità dei Dati
- **Fonti affidabili**: Reuters, Bloomberg, CNBC, MarketWatch
- **Aggiornamenti real-time**: News pubblicate entro minuti
- **Copertura globale**: Mercati internazionali inclusi

## 🛠️ Installazione e Configurazione

### 1. Ottenere API Key Alpha Vantage

1. Vai su [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Registrati per un account gratuito
3. Genera la tua API key
4. **Nota**: Piano gratuito: 5 chiamate/minuto, 500/giorno

### 2. Configurazione Rapida

```bash
# Crea un file di configurazione di esempio
cargo run -- create-config

# Modifica il file config.toml e aggiungi la tua API key
# Poi testa l'integrazione
cargo run -- test-alpha-vantage --demo
```

### 3. Configurazione Manuale

Copia `alpha_vantage_example.toml` in `config.toml`:

```toml
[data_collection]
mode = "Prod"  # Usa "Demo" per test senza API

[[data_collection.sources]]
name = "Alpha Vantage News"
platform = "AlphaVantage"
url = "https://www.alphavantage.co/query"
api_key = "LA_TUA_API_KEY_QUI"
enabled = true

[data_collection.filters]
keywords = ["finance", "economy", "crypto", "stocks", "earnings"]
languages = ["en"]
```

## 🎯 Utilizzo

### Modalità CLI

```bash
# Test rapido (modalità demo)
cargo run -- test-alpha-vantage --demo

# Test con API key
cargo run -- test-alpha-vantage --api-key YOUR_KEY

# Validazione configurazione
cargo run -- validate-config

# Raccolta dati completa
cargo run -- collect-data --demo
```

### Modalità GUI

```bash
# Avvia l'interfaccia grafica
cargo run
```

Nella GUI, seleziona "Alpha Vantage" come piattaforma e imposta la modalità "Production".

## 📊 Struttura dei Dati

### News Item
```rust
pub struct AlphaVantageNewsItem {
    pub title: String,                    // Titolo della news
    pub url: String,                      // URL dell'articolo
    pub time_published: String,           // Timestamp di pubblicazione
    pub authors: Vec<String>,             // Autori dell'articolo
    pub summary: String,                  // Riassunto dell'articolo
    pub overall_sentiment_score: f64,     // Punteggio sentiment (-1.0 a 1.0)
    pub overall_sentiment_label: String,  // Etichetta sentiment
    pub ticker_sentiment: Vec<AlphaVantageTickerSentiment>, // Sentiment per ticker
}
```

### Esempi di Utilizzo

#### 1. Monitoraggio Crypto
```toml
[data_collection.filters]
keywords = ["bitcoin", "ethereum", "crypto", "blockchain", "defi"]
```

#### 2. Analisi Earnings
```toml
[data_collection.filters]
keywords = ["earnings", "revenue", "profit", "quarterly", "guidance"]
```

#### 3. Monitoraggio Fed
```toml
[data_collection.filters]
keywords = ["fed", "federal reserve", "interest rate", "monetary policy"]
```

## 🔧 Comandi CLI Disponibili

### Test Alpha Vantage
```bash
cargo run -- test-alpha-vantage [OPTIONS]

Options:
  -c, --config <FILE>     File di configurazione [default: config.toml]
  --api-key <KEY>         API key di Alpha Vantage
  --demo                  Modalità demo (senza chiamate API reali)
```

### Creazione Configurazione
```bash
cargo run -- create-config [OUTPUT]

Arguments:
  <OUTPUT>  Percorso del file di configurazione [default: config.toml]
```

### Validazione Configurazione
```bash
cargo run -- validate-config [CONFIG]

Arguments:
  <CONFIG>  File di configurazione da validare [default: config.toml]
```

### Raccolta Dati
```bash
cargo run -- collect-data [OPTIONS]

Options:
  -c, --config <FILE>  File di configurazione [default: config.toml]
  --demo               Modalità demo
```

## 📈 Esempi di Output

### Test Rapido
```
🧪 Test Alpha Vantage Integration
==================================
✅ Configurazione valida
📊 Testando raccolta dati...
✅ Raccolta completata!
📈 Dati raccolti: 45 punti

📊 Analisi Rapida
================
📱 Piattaforme:
   AlphaVantage: 45 (100.0%)

😊 Sentiment medio: 0.234
   Classificazione: 🟢 Positivo
```

### Analisi Dettagliata
```
📊 Analisi Dettagliata
=====================
📱 Distribuzione per Piattaforma:
   AlphaVantage: 45 (100.0%)

🎯 Distribuzione per Tema:
   Economy: 32 (71.1%)
   Technology: 8 (17.8%)
   Politics: 5 (11.1%)

😊 Sentiment Analysis:
   Media: 0.234
   Punti con sentiment: 45/45
   Classificazione: 🟢 Positivo

📈 Engagement medio: 156.7 interazioni per punto
```

## ⚠️ Limitazioni e Considerazioni

### Rate Limiting
- **Piano gratuito**: 5 chiamate/minuto, 500/giorno
- **Strategia**: Implementare caching e rate limiting
- **Monitoraggio**: Logga le chiamate per debugging

### Copertura Linguistica
- **Primariamente inglese**: La maggior parte delle news sono in inglese
- **Traduzione**: Considerare servizi di traduzione per altre lingue

### Storico Limitato
- **News recenti**: Generalmente ultimi 7-30 giorni
- **Archiviazione**: Implementare storage locale per dati storici

## 🔍 Troubleshooting

### Problemi Comuni

1. **"Error Message" nella risposta**
   - Verifica la validità dell'API key
   - Controlla i limiti di rate

2. **"Note" nella risposta**
   - Raggiunto il limite di chiamate
   - Aspetta prima di fare nuove richieste

3. **Nessun dato raccolto**
   - Verifica i filtri keywords
   - Controlla la connessione di rete
   - Fallback automatico a dati simulati

### Debug

Abilita il logging dettagliato:
```rust
tracing_subscriber::fmt()
    .with_max_level(tracing::Level::DEBUG)
    .init();
```

## 🚀 Sviluppi Futuri

### Possibili Miglioramenti
1. **Supporto multi-lingua**: Integrazione con servizi di traduzione
2. **Caching avanzato**: Database locale per dati storici
3. **Analisi real-time**: WebSocket per aggiornamenti live
4. **Integrazione con altri servizi**: Combinare con altre API finanziarie

### Estensioni
1. **Alert personalizzati**: Notifiche per sentiment specifici
2. **Dashboard avanzata**: Visualizzazioni interattive
3. **Backtesting**: Test di strategie su dati storici
4. **Machine Learning**: Modelli predittivi basati su sentiment

## 📚 Documentazione Aggiuntiva

- [ALPHA_VANTAGE_INTEGRATION.md](ALPHA_VANTAGE_INTEGRATION.md) - Documentazione tecnica dettagliata
- [alpha_vantage_example.toml](alpha_vantage_example.toml) - File di configurazione di esempio
- [examples/test_alpha_vantage.rs](examples/test_alpha_vantage.rs) - Esempio di codice

## 🤝 Contributi

Per contribuire all'integrazione Alpha Vantage:

1. Fork del repository
2. Crea un branch per la feature
3. Implementa le modifiche
4. Aggiungi test
5. Invia una Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file [LICENSE](LICENSE) per i dettagli. 