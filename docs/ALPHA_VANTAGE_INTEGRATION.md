# Integrazione Alpha Vantage per DollarPunk

Questo documento descrive come utilizzare l'integrazione con Alpha Vantage per l'ingestione di dati news finanziari nel progetto DollarPunk.

## 🚀 Panoramica

Alpha Vantage è un'API che fornisce dati finanziari in tempo reale, inclusi:
- News e sentiment analysis
- Dati di mercato (prezzi, volumi, etc.)
- Indicatori tecnici
- Dati economici

## 📋 Prerequisiti

1. **API Key Alpha Vantage**: Ottieni una API key gratuita da [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. **Rust**: Assicurati di avere Rust installato (versione 1.70+)

## 🔧 Configurazione

### 1. Imposta la variabile d'ambiente

```bash
# Windows PowerShell
$env:ALPHA_VANTAGE_API_KEY="your_api_key_here"

# Windows CMD
set ALPHA_VANTAGE_API_KEY=your_api_key_here

# Linux/macOS
export ALPHA_VANTAGE_API_KEY="your_api_key_here"
```

### 2. Configurazione nel codice

```rust
use dollar_punk::alpha_vantage::{AlphaVantageClient, AlphaVantageConfig};

let config = AlphaVantageConfig {
    api_key: "your_api_key_here".to_string(),
    base_url: "https://www.alphavantage.co/query".to_string(),
    rate_limit_delay_ms: 12000, // 5 richieste al minuto per il tier gratuito
    max_requests_per_minute: 5,
};

let mut client = AlphaVantageClient::new(config);
```

## 📊 Utilizzo

### Raccolta News con Sentiment Analysis

```rust
use dollar_punk::models::DataFilters;

let filters = DataFilters {
    keywords: vec![
        "economy".to_string(),
        "finance".to_string(),
        "crypto".to_string(),
        "bitcoin".to_string(),
    ],
    languages: vec!["en".to_string(), "it".to_string()],
    min_engagement: 0,
    exclude_retweets: false,
    exclude_ads: true,
};

let news_data = client.collect_news_data(&filters).await?;
```

### Raccolta Dati di Mercato

```rust
let market_data = client.get_market_data("BTCUSD").await?;
// Restituisce: HashMap<String, f64> con price, change, change_percent
```

### Integrazione con DataCollector

```rust
use dollar_punk::data_collector::DataCollector;

let mut collector = DataCollector::new()
    .with_alpha_vantage("your_api_key_here".to_string());

let config = DataCollectionConfig::default();
let data = collector.collect_data(&config).await?;
```

## 🏃‍♂️ Esempi

### Esegui l'esempio completo

```bash
cargo run --example alpha_vantage_example
```

### Output dell'esempio

```
🚀 Esempio di utilizzo di Alpha Vantage per l'ingestione di dati news
📰 Raccolta dati news da Alpha Vantage...
🔍 Keywords: ["economy", "finance", "crypto", "bitcoin", "ethereum"]
🌍 Lingue: ["en", "it"]
✅ Raccolti 45 articoli news

--- Articolo 1 ---
📝 Titolo: Bitcoin Surges Past $50,000 as Institutional Adoption Grows
👤 Autore: John Smith, Financial Times
📅 Data: 2024-01-15 14:30:00 UTC
🏷️  Tema: Economy
🌍 Lingua: en
😊 Sentiment: 0.234
🔗 URL: https://example.com/article1

📊 Distribuzione per tema:
  Economy: 25 articoli
  Technology: 12 articoli
  Politics: 8 articoli

😊 Sentiment medio: 0.156
  Positivi: 18 (40.0%)
  Negativi: 12 (26.7%)
  Neutri: 15 (33.3%)

📈 Raccolta dati di mercato per Bitcoin...
✅ Dati di mercato Bitcoin:
  price: 50123.45
  change: 1234.56
  change_percent: 2.53
```

## 📈 Funzionalità Disponibili

### News & Sentiment Analysis
- **Endpoint**: `NEWS_SENTIMENT`
- **Limite**: 50 articoli per richiesta (tier gratuito)
- **Dati inclusi**:
  - Titolo e riassunto
  - Autori
  - Data di pubblicazione
  - URL dell'articolo
  - Sentiment score (-1.0 a +1.0)
  - Sentiment label (positive/negative/neutral)
  - Topics e relevance scores

### Market Data
- **Endpoint**: `GLOBAL_QUOTE`
- **Dati disponibili**:
  - Prezzo corrente
  - Variazione giornaliera
  - Percentuale di variazione
  - Volume
  - Prezzi di apertura/chiusura

## ⚠️ Limitazioni

### Rate Limiting
- **Tier gratuito**: 5 richieste al minuto
- **Tier premium**: 500+ richieste al minuto
- Il client gestisce automaticamente il rate limiting

### Quota API
- **Tier gratuito**: 500 richieste al giorno
- **Tier premium**: Richieste illimitate

### Dati Storici
- I dati news sono limitati agli ultimi 7 giorni
- I dati di mercato sono in tempo reale

## 🔍 Struttura Dati

### AlphaVantageNewsItem
```rust
pub struct AlphaVantageNewsItem {
    pub title: String,
    pub url: String,
    pub time_published: String,
    pub authors: Vec<String>,
    pub summary: String,
    pub banner_image: Option<String>,
    pub source: String,
    pub category_within_source: String,
    pub source_domain: String,
    pub topics: Vec<AlphaVantageTopic>,
    pub overall_sentiment_score: Option<f64>,
    pub overall_sentiment_label: Option<String>,
}
```

### Conversione in DataPoint
Il client converte automaticamente i dati Alpha Vantage nel formato `DataPoint` utilizzato da DollarPunk:

```rust
DataPoint {
    id: "alpha_vantage_0",
    content: "Titolo - Riassunto",
    platform: Platform::NewsWebsite,
    timestamp: DateTime<Utc>,
    theme: Theme::Economy,
    author: "Autori",
    url: Some("URL articolo"),
    engagement_metrics: EngagementMetrics::default(),
    language: "en",
    sentiment_score: Some(0.234),
}
```

## 🛠️ Troubleshooting

### Errore "API key not found"
- Verifica che la API key sia corretta
- Assicurati che la variabile d'ambiente sia impostata

### Errore "Rate limit exceeded"
- Il client gestisce automaticamente il rate limiting
- Se persiste, aumenta `rate_limit_delay_ms`

### Nessun dato restituito
- Verifica che le keywords siano corrette
- Controlla che la lingua sia supportata
- Verifica la quota API giornaliera

### Errore di parsing JSON
- L'API potrebbe aver cambiato formato
- Controlla i log per dettagli

## 🔗 Risorse Utili

- [Documentazione Alpha Vantage](https://www.alphavantage.co/documentation/)
- [API Key Registration](https://www.alphavantage.co/support/#api-key)
- [Rate Limiting Info](https://www.alphavantage.co/premium/)
- [News & Sentiment API](https://www.alphavantage.co/documentation/#news-sentiment)

## 📝 Note di Sviluppo

### Gestione Rate Limiting
Il client implementa un sistema di rate limiting intelligente:
- Conta le richieste per minuto
- Attende automaticamente quando necessario
- Resetta il contatore ogni minuto

### Error Handling
- Gestione robusta degli errori HTTP
- Fallback a dati simulati se l'API non è disponibile
- Logging dettagliato per debugging

### Performance
- Richieste asincrone con `tokio`
- Caching opzionale dei risultati
- Parsing efficiente dei JSON 