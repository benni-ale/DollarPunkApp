# DollarPunk - Social Media Data Collection & Stratification

DollarPunk è un'applicazione desktop per la raccolta e stratificazione di dati dai social media, progettata per analisi finanziarie e di mercato.

## Caratteristiche Principali

### 🎮 Modalità Demo Avanzata
La modalità demo è stata completamente riprogettata per generare dati **realistici e applicabili nella vita reale**:

#### **Contenuti Realistici**
- **Eventi di mercato reali**: Earnings, decisioni Fed, dati economici, rally crypto, crash di mercato, fusioni
- **Aziende reali**: Apple, Tesla, Microsoft, Amazon, Google, Meta, NVIDIA, AMD, Intel
- **Progetti crypto reali**: Bitcoin, Ethereum, Cardano, Solana, Polkadot, Chainlink
- **Scenari finanziari realistici**: Prezzi azionari, indicatori economici, tassi di interesse, inflazione

#### **Pattern Temporali Realistici**
- **Orari di mercato**: Maggiore attività durante gli orari di trading (9:30 AM - 4:00 PM ET)
- **Effetti weekend**: Ridotta attività nei fine settimana
- **Distribuzione temporale**: Post più recenti hanno maggiore engagement

#### **Metriche di Engagement Sofisticate**
- **Pattern per piattaforma**: Twitter (alto engagement), Reddit (molti commenti), News (molte condivisioni)
- **Fattori virali**: 5% chance di post virali, 15% chance di post trending
- **Correlazione sentiment**: Contenuti positivi/negativi influenzano l'engagement
- **Fattori temporali**: Post recenti ottengono più engagement

#### **Analisi del Sentiment Avanzata**
- **Sentiment basato su temi**: Economia (misto), Tech (positivo), Politica (negativo)
- **Keyword analysis**: "breaking", "surge", "crash", "growth", "beat", "miss"
- **Sentiment di mercato**: "bullish", "bearish", "neutral"
- **Sentiment crypto**: Adozione istituzionale, regolamentazione

#### **Eventi di Mercato Correlati**
- **Eventi che influenzano multipli post**: 30% dei post sono correlati a eventi di mercato
- **Volatilità di mercato**: Influenza il volume di post generati
- **Correlazioni tra piattaforme**: Eventi simili su diverse piattaforme

### 📊 Stratificazione Intelligente
- Creazione automatica di strati basati su piattaforma, tema e periodo temporale
- Campionamento bilanciato per garantire rappresentatività
- Statistiche dettagliate sulla distribuzione dei dati

### 🎯 Filtri Avanzati
- Filtri per parole chiave, lingue, engagement minimo
- Esclusione di retweet e pubblicità
- Configurazione flessibile per diverse esigenze analitiche

### 📈 Esportazione Dati
- Esportazione in formato CSV e JSON
- Timestamp automatici per i file esportati
- Statistiche complete sui dati campionati

## Installazione

### Prerequisiti
- Rust 1.70+ (https://rustup.rs/)
- Windows 10/11, macOS, o Linux

### Compilazione
```bash
git clone https://github.com/yourusername/DollarPunk.git
cd DollarPunk
cargo build --release
```

### Esecuzione
```bash
cargo run
```

## Utilizzo

### 1. Configurazione Raccolta Dati
- Seleziona la **modalità Demo** per testare con dati realistici
- Configura le fonti dati (Twitter, Reddit, News, RSS)
- Imposta filtri per parole chiave e lingue
- Definisci il periodo di raccolta

### 2. Raccolta Dati
- Clicca "Start Collection" per avviare la raccolta
- Monitora il progresso in tempo reale
- Visualizza i log dettagliati per debugging

### 3. Stratificazione
- Configura i pesi per piattaforme e temi
- Imposta parametri di campionamento
- Crea gli strati e campiona i dati

### 4. Analisi Risultati
- Visualizza statistiche sulla stratificazione
- Esplora i dati campionati
- Esporta i risultati per analisi esterne

## Esempi di Dati Demo Generati

### Twitter - Contenuti Realistici
```
"BREAKING: Apple stock surges 15% after earnings beat! Q4 revenue up 25% YoY. Analysts upgrading price targets. #finance #stocks #earnings"

"CPI data: 3.2% YoY inflation, higher than expected. Core inflation at 4.1%. Market implications? #economy #inflation #markets"

"Bitcoin just hit $45K! 🚀 Market cap now $850B. Institutional adoption accelerating. #crypto #bitcoin #markets"
```

### Reddit - Discussioni Realistiche
```
"What's everyone's thoughts on Tesla? I've been following it for a while and the recent developments are interesting."

"Discussion: crypto market analysis and predictions for Q1. What are your positions?"

"BREAKING: Microsoft just announced AI partnership. How will this affect the market?"
```

### News - Articoli Professionali
```
"Market Analysis: tech sector shows strong momentum as investors focus on growth opportunities. Expert analysis suggests continued upward trend."

"Economic Update: inflation indicators point to robust recovery. Central bank policies supporting market stability."

"Technology Trends: AI innovation driving market transformation. Industry leaders adapt to changing landscape."
```

## Architettura Tecnica

### Componenti Principali
- **GUI**: Interfaccia grafica con egui
- **Data Collector**: Raccolta dati da multiple fonti
- **Stratification Engine**: Algoritmi di stratificazione
- **Models**: Strutture dati e configurazioni

### Tecnologie Utilizzate
- **Rust**: Linguaggio principale
- **egui**: Framework GUI
- **tokio**: Runtime asincrono
- **serde**: Serializzazione JSON
- **chrono**: Gestione date e orari
- **rand**: Generazione numeri casuali

## Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## Roadmap

### Prossime Funzionalità
- [ ] Integrazione API reali (Twitter, Reddit, News)
- [ ] Analisi sentiment con ML
- [ ] Dashboard interattiva per visualizzazioni
- [ ] Supporto per più lingue
- [ ] Esportazione in più formati (Excel, Parquet)
- [ ] Schedulazione automatica della raccolta
- [ ] Alert e notifiche per eventi di mercato

### Miglioramenti Demo
- [ ] Più eventi di mercato specifici
- [ ] Correlazioni tra eventi e sentiment
- [ ] Pattern stagionali e ciclici
- [ ] Simulazione di trend di mercato
- [ ] Eventi geopolitici e loro impatto 