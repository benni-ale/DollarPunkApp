# Integrazione Alpha Vantage con DollarPunk

## Panoramica

Alpha Vantage è un'API che fornisce dati finanziari e news con sentiment analysis già integrata. Questa integrazione permette a DollarPunk di raccogliere news finanziarie con punteggi di sentiment pre-calcolati, migliorando significativamente la qualità dell'analisi.

## Vantaggi dell'Integrazione Alpha Vantage

### 1. Sentiment Analysis Pre-calcolata
- **Punteggi di sentiment accurati**: Alpha Vantage utilizza algoritmi avanzati di NLP per calcolare il sentiment
- **Risparmio di risorse**: Non è necessario implementare analisi del sentiment in locale
- **Consistenza**: Metodologia uniforme per tutti i punteggi di sentiment

### 2. Dati Finanziari Specializzati
- **News finanziarie curate**: Contenuti specifici per il mercato finanziario
- **Categorizzazione automatica**: News classificate per argomenti e settori
- **Analisi per ticker**: Sentiment specifico per singole azioni/cryptocurrency

### 3. Qualità dei Dati
- **Fonti affidabili**: Reuters, Bloomberg, CNBC, MarketWatch, etc.
- **Aggiornamenti in tempo reale**: News pubblicate entro minuti
- **Copertura globale**: Mercati internazionali inclusi

## Configurazione

### 1. Ottenere un API Key

1. Vai su [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Registrati per un account gratuito
3. Genera la tua API key
4. **Nota**: Il piano gratuito ha limiti di 5 chiamate al minuto e 500 al giorno

### 2. Configurare DollarPunk

Copia il file `alpha_vantage_example.toml` in `config.toml` e modifica:

```toml
[[data_collection.sources]]
name = "Alpha Vantage News"
platform = "AlphaVantage"
url = "https://www.alphavantage.co/query"
api_key = "LA_TUA_API_KEY_QUI"
enabled = true
```

### 3. Personalizzare i Filtri

```toml
[data_collection.filters]
keywords = ["finance", "economy", "crypto", "stocks", "earnings", "fed", "inflation"]
languages = ["en"]
min_engagement = 10
```

## Struttura dei Dati Alpha Vantage

### News Item
```rust
pub struct AlphaVantageNewsItem {
    pub title: String,                    // Titolo della news
    pub url: String,                      // URL dell'articolo
    pub time_published: String,           // Timestamp di pubblicazione
    pub authors: Vec<String>,             // Autori dell'articolo
    pub summary: String,                  // Riassunto dell'articolo
    pub banner_image: Option<String>,     // Immagine di copertina
    pub source: String,                   // Fonte (Reuters, Bloomberg, etc.)
    pub category_within_source: String,   // Categoria nella fonte
    pub source_domain: String,            // Dominio della fonte
    pub topics: Vec<AlphaVantageTopic>,   // Argomenti correlati
    pub overall_sentiment_score: f64,     // Punteggio sentiment (-1.0 a 1.0)
    pub overall_sentiment_label: String,  // Etichetta sentiment (Bearish/Bullish/Neutral)
    pub ticker_sentiment: Vec<AlphaVantageTickerSentiment>, // Sentiment per ticker specifici
}
```

### Ticker Sentiment
```rust
pub struct AlphaVantageTickerSentiment {
    pub ticker: String,                   // Simbolo del ticker (AAPL, BTC, etc.)
    pub relevance_score: String,          // Rilevanza del ticker nell'articolo
    pub ticker_sentiment_score: String,   // Sentiment specifico per il ticker
    pub ticker_sentiment_label: String,   // Etichetta sentiment per il ticker
}
```

## Utilizzo nell'Applicazione

### 1. Modalità Demo vs Produzione

- **Demo**: Genera dati simulati per test e sviluppo
- **Prod**: Utilizza l'API reale di Alpha Vantage

```toml
[data_collection]
mode = "Prod"  # Cambia in "Demo" per test senza API key
```

### 2. Gestione degli Errori

L'applicazione gestisce automaticamente:
- **Rate limiting**: Rispetta i limiti dell'API
- **Errori di rete**: Fallback a dati simulati
- **API key invalida**: Avvisi e fallback
- **Dati mancanti**: Generazione di dati realistici

### 3. Filtri Avanzati

```rust
// Esempio di filtri personalizzati
let filters = DataFilters {
    keywords: vec!["bitcoin".to_string(), "ethereum".to_string()],
    languages: vec!["en".to_string()],
    min_engagement: 50,
    exclude_retweets: true,
    exclude_ads: true,
};
```

## Esempi di Utilizzo

### 1. Raccolta News Crypto
```toml
[data_collection.filters]
keywords = ["bitcoin", "ethereum", "crypto", "blockchain", "defi"]
```

### 2. Analisi Earnings
```toml
[data_collection.filters]
keywords = ["earnings", "revenue", "profit", "quarterly", "guidance"]
```

### 3. Monitoraggio Fed
```toml
[data_collection.filters]
keywords = ["fed", "federal reserve", "interest rate", "monetary policy"]
```

## Limitazioni e Considerazioni

### 1. Rate Limiting
- **Piano gratuito**: 5 chiamate/minuto, 500/giorno
- **Piano premium**: Limiti più alti disponibili
- **Strategia**: Implementare caching e rate limiting

### 2. Copertura Linguistica
- **Primariamente inglese**: La maggior parte delle news sono in inglese
- **Traduzione**: Considerare servizi di traduzione per altre lingue

### 3. Storico Limitato
- **News recenti**: Generalmente ultimi 7-30 giorni
- **Archiviazione**: Implementare storage locale per dati storici

## Best Practices

### 1. Gestione API Key
```bash
# Usa variabili d'ambiente per sicurezza
export ALPHA_VANTAGE_API_KEY="your_key_here"
```

### 2. Caching
- Implementa cache locale per ridurre chiamate API
- Salva dati per analisi offline
- Rispetta i limiti di rate

### 3. Monitoraggio
- Logga le chiamate API per debugging
- Monitora l'utilizzo per evitare limiti
- Implementa alert per errori

## Troubleshooting

### Problemi Comuni

1. **"Error Message" nella risposta**
   - Verifica la validità dell'API key
   - Controlla i limiti di rate

2. **"Note" nella risposta**
   - Raggiunto il limite di chiamate
   - Aspetta prima di fare nuove richieste

3. **Nessun dato ricevuto**
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

## Sviluppi Futuri

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