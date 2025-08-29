# DollarPunk - Software Portafoglio

Software per la gestione e analisi di portafogli di investimento con dati real-time da Alpha Vantage API.

## 🚀 Caratteristiche

- **Dashboard interattiva** con metriche in tempo reale
- **Gestione portafogli personalizzati** con posizioni multiple
- **Dati real-time** da Alpha Vantage API
- **Autenticazione utenti** con sistema di login
- **Database PostgreSQL** per scalabilità
- **Autocompletamento ticker** con 12.000+ simboli
- **Prezzi storici automatici** basati su data di acquisto
- **Interfaccia moderna** con tema scuro

## 🛠️ Tecnologie

- **Backend:** Flask (Python)
- **Database:** PostgreSQL con SQLAlchemy ORM
- **Frontend:** HTML5, CSS3, JavaScript vanilla
- **API:** Alpha Vantage per dati finanziari
- **Containerizzazione:** Docker & Docker Compose

## 📋 Prerequisiti

- Docker e Docker Compose
- Alpha Vantage API Key (gratuita)

## ⚙️ Installazione

### 1. Clona il Repository
```bash
git clone <repository-url>
cd DollarPunk/web
```

### 2. Configura le Variabili d'Ambiente
Crea un file `.env` nella root del progetto (non in `web/`):
```bash
# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Secret Key per Flask
SECRET_KEY=your_secret_key_here

# Database PostgreSQL (opzionale)
DATABASE_URL=postgresql://dollarpunk_user:dollarpunk_password@postgres:5432/dollarpunk
```

### 3. Avvia l'Applicazione
```bash
docker-compose up --build
```

### 4. Accedi all'App
- URL: http://localhost:5000
- **Credenziali demo:** `demo@dollarpunk.com` / `demo123`

## 🗄️ Database PostgreSQL

L'applicazione utilizza PostgreSQL per:
- **Utenti:** Gestione account e autenticazione
- **Portafogli:** Posizioni personalizzate degli utenti
- **Scalabilità:** Supporto per migliaia di utenti

### Struttura Database
- **`users`:** Informazioni utenti (email, password hash, nome)
- **`portfolio_positions`:** Posizioni portafoglio (simbolo, quantità, prezzo medio, data acquisto)

### Migrazione da JSON
Gli utenti esistenti con portafogli JSON verranno migrati automaticamente al database PostgreSQL.

## 📊 Funzionalità

### Gestione Portafoglio
- ✅ **Aggiungi posizioni** con autocompletamento ticker
- ✅ **Modifica posizioni** esistenti
- ✅ **Rimuovi posizioni** dal portafoglio
- ✅ **Prezzi storici automatici** basati su data di acquisto
- ✅ **Calcolo performance** in tempo reale

### Dashboard
- 📈 **Metriche portfolio** (valore totale, performance YTD, dividendi)
- 📊 **Allocazione asset** (azioni, obbligazioni, cash)
- 📋 **Tabella posizioni** con azioni rapide
- 🔄 **Aggiornamento dati** in tempo reale

### Autenticazione
- 🔐 **Login/logout** con sessioni sicure
- 👤 **Account demo** per test
- 🛡️ **Protezione route** con decoratori

## 🔧 Sviluppo

### Struttura Progetto
```
web/
├── app.py              # Applicazione Flask principale
├── models.py           # Modelli SQLAlchemy
├── database.py         # Funzioni database
├── requirements.txt    # Dipendenze Python
├── docker-compose.yml  # Configurazione Docker
├── Dockerfile         # Immagine Docker
├── static/
│   └── style.css      # Stili CSS
├── templates/         # Template HTML
│   ├── index.html     # Landing page
│   ├── login.html     # Pagina login
│   └── portfolio-software.html  # Dashboard principale
└── symbols.csv        # Lista ticker per autocompletamento
```

### Comandi Utili
```bash
# Avvia in modalità sviluppo
docker-compose up --build

# Visualizza log
docker-compose logs -f

# Ricostruisci container
docker-compose down && docker-compose up --build

# Accedi al database
docker-compose exec postgres psql -U dollarpunk_user -d dollarpunk
```

## 🌐 API Endpoints

### Portfolio
- `GET /api/portfolio` - Dati portfolio utente
- `POST /api/portfolio/add` - Aggiungi posizione
- `POST /api/portfolio/update` - Modifica posizione
- `POST /api/portfolio/remove` - Rimuovi posizione

### Titoli
- `GET /api/stock/<symbol>` - Dati singolo titolo
- `GET /api/search?q=<query>` - Ricerca ticker
- `GET /api/tickers` - Lista completa ticker

### Debug
- `GET /api/test` - Test API
- `GET /api/debug/routes` - Lista route
- `GET /api/debug/session` - Stato sessione

## 🔒 Sicurezza

- **Password hashate** con Werkzeug
- **Sessioni sicure** con secret key
- **Validazione input** su tutti gli endpoint
- **Rate limiting** per Alpha Vantage API
- **Protezione CSRF** (da implementare)

## 📈 Scalabilità

### Database
- **PostgreSQL** per performance e affidabilità
- **Indici ottimizzati** per query frequenti
- **Connection pooling** per connessioni multiple

### API
- **Rate limiting** per Alpha Vantage (5 calls/min)
- **Caching** per dati statici (da implementare)
- **Async processing** per operazioni pesanti (da implementare)

## 🚀 Roadmap

- [ ] **Registrazione utenti** con email verification
- [ ] **Recupero password** con reset via email
- [ ] **Notifiche** per eventi portfolio
- [ ] **Export dati** in CSV/PDF
- [ ] **Grafici interattivi** con Chart.js
- [ ] **Mobile app** React Native
- [ ] **WebSocket** per aggiornamenti real-time
- [ ] **Multi-tenant** per consulenti finanziari

## 📝 Licenza

Demo software - non rappresenta un servizio finanziario reale.

## 🤝 Contributi

1. Fork il progetto
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

---

**DollarPunk** - Gestione portafogli intelligente 🚀
