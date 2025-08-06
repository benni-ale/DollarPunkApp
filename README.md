# DollarPunk - Social Media Data Collection & Stratification

DollarPunk è un'applicazione GUI in Rust per raccogliere dati da social media e news, applicare stratificazione e campionamento bilanciato per l'analisi del sentiment.

## Caratteristiche

- **Raccolta Dati Multi-Piattaforma**: Supporto per Twitter, Facebook, Reddit, RSS feeds e siti di news
- **Stratificazione Avanzata**: Raggruppamento per piattaforma, tema e periodo temporale
- **Campionamento Bilanciato**: Algoritmi di campionamento per garantire rappresentatività
- **Interfaccia Grafica Moderna**: GUI intuitiva costruita con egui
- **Esportazione Dati**: Esportazione in CSV e JSON per analisi successive
- **Filtri Personalizzabili**: Filtri per keywords, lingue, engagement e altro

## Installazione

### Prerequisiti

- Rust 1.70+ e Cargo
- Connessione internet per la raccolta dati

### Build

```bash
# Clona il repository
git clone <repository-url>
cd DollarPunk

# Build dell'applicazione
cargo build --release

# Esegui l'applicazione
cargo run --release
```

## Utilizzo

### 1. Configurazione Raccolta Dati

Nella tab "Data Collection":

- **Data Sources**: Configura le fonti di dati (Twitter, RSS, siti news, etc.)
- **Filters**: Imposta keywords, lingue e filtri di engagement
- **Collection Period**: Definisci il periodo di raccolta dati

### 2. Avvio Raccolta

- Clicca "Start Collection" per iniziare la raccolta
- Monitora il progresso e lo stato nella barra di stato
- I dati raccolti vengono mostrati nel riepilogo

### 3. Stratificazione

Nella tab "Stratification":

- **Platform Weights**: Imposta i pesi per le diverse piattaforme
- **Theme Weights**: Configura i pesi per i temi (Economia, Politica, etc.)
- **Sampling Parameters**: Definisci i parametri di campionamento

### 4. Campionamento

- Clicca "Create Strata" per creare gli strati
- Clicca "Sample Data" per eseguire il campionamento bilanciato
- Visualizza i risultati nella tab "Results"

### 5. Esportazione

- I dati campionati vengono automaticamente esportati in CSV
- Opzione per esportazione aggiuntiva in JSON
- I file vengono salvati nella cartella `./exports/`

## Struttura del Progetto

```
src/
├── main.rs              # Entry point dell'applicazione
├── models.rs            # Modelli di dati e strutture
├── data_collector.rs    # Logica di raccolta dati
├── stratification.rs    # Engine di stratificazione e campionamento
└── gui.rs              # Interfaccia grafica
```

## Configurazione Avanzata

### Fonti Dati Personalizzate

Puoi aggiungere nuove fonti di dati modificando la configurazione:

```rust
DataSource {
    name: "My Custom Source",
    platform: Platform::Other("Custom"),
    url: "https://example.com",
    api_key: Some("your-api-key"),
    enabled: true,
}
```

### Filtri Personalizzati

Configura filtri per:
- Keywords specifiche
- Lingue (it, en, etc.)
- Engagement minimo
- Esclusione retweet/ads

### Stratificazione Personalizzata

Modifica i pesi per:
- Piattaforme diverse
- Temi specifici
- Periodi temporali

## Formato Dati Esportati

### CSV Output

```csv
id,content,platform,theme,author,timestamp,language,likes,shares,comments,views,sentiment_score,url
```

### JSON Output

```json
[
  {
    "id": "twitter_123",
    "content": "Sample content...",
    "platform": "Twitter",
    "theme": "Economy",
    "author": "user_1234",
    "timestamp": "2024-01-01T12:00:00Z",
    "language": "en",
    "engagement_metrics": {
      "likes": 100,
      "shares": 50,
      "comments": 25,
      "views": 1000
    },
    "sentiment_score": 0.5,
    "url": "https://twitter.com/..."
  }
]
```

## Analisi del Sentiment

I dati esportati includono:
- **Sentiment Score**: Valore da -1.0 (negativo) a +1.0 (positivo)
- **Engagement Metrics**: Likes, shares, comments, views
- **Metadata**: Piattaforma, tema, autore, timestamp

## Limitazioni Attuali

- Raccolta dati simulata per alcune piattaforme (richiede API keys reali)
- Rate limiting implementato per rispettare i limiti delle API
- Supporto limitato per alcune piattaforme social

## Sviluppo Futuro

- [ ] Integrazione API reali per Twitter, Facebook, etc.
- [ ] Analisi del sentiment più avanzata
- [ ] Visualizzazioni grafiche dei risultati
- [ ] Supporto per più lingue nell'interfaccia
- [ ] Database per caching dei dati

## Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## Supporto

Per domande o problemi:
- Apri una issue su GitHub
- Contatta il team di sviluppo

---

**DollarPunk** - Potente strumento per l'analisi dei social media e news con stratificazione avanzata. 