# DollarPunk Web Application

Applicazione web per la gestione del portafoglio azionario con supporto multi-valuta e classificazione GICS.

## 🚀 Avvio con Docker Compose

```bash
docker-compose up --build
```

L'applicazione si avvia automaticamente senza richiedere interventi manuali. La classificazione GICS viene gestita tramite il file CSV `symbol,gics_cat.csv` che contiene oltre 300 titoli classificati secondo lo standard GICS ufficiale.

## 🔧 Configurazione

### Variabili d'Ambiente
Crea un file `.env` nella root del progetto con:

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://dollarpunk_user:dollarpunk_password@postgres:5432/dollarpunk
```

### Chiave API Alpha Vantage
1. Registrati su [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Ottieni la tua chiave API gratuita
3. Aggiungila al file `.env`

## 📊 Funzionalità

### Multi-Valuta
- Supporto per EUR, USD, GBP, CHF e altre valute
- Conversione automatica dei prezzi
- Tassi di cambio storici per calcoli accurati

### Classificazione GICS
- 11 settori ufficiali GICS (Global Industry Classification Standard)
- 300+ titoli pre-classificati tramite file CSV
- Fallback a mappatura statica per titoli non nel CSV

### Portfolio Management
- Aggiunta/rimozione posizioni
- Calcolo automatico di profitti/perdite
- Visualizzazione prezzi in valuta locale e convertiti

## 🗄️ Database

L'applicazione utilizza PostgreSQL per:
- **Utenti**: Gestione account e autenticazione
- **Portfolio**: Posizioni azionarie personali

La classificazione GICS viene gestita tramite il file CSV `symbol,gics_cat.csv` che contiene oltre 300 titoli classificati secondo lo standard ufficiale GICS.

```

## 🔍 API Endpoints

### Portfolio
- `GET /api/portfolio?currency=EUR` - Dati portfolio con conversione valuta
- `POST /api/portfolio/add` - Aggiungi posizione
- `POST /api/portfolio/remove` - Rimuovi posizione
- `POST /api/portfolio/update` - Aggiorna posizione

### Settori GICS
- `GET /api/sector/<symbol>` - Info settore per un titolo
- `GET /api/sectors` - Lista tutti i settori disponibili

### Valute
- `GET /api/exchange-rates` - Tassi di cambio supportati
- `GET /api/currency-info` - Info performance valute

## 👤 Credenziali Demo

- **Email**: `demo@dollarpunk.com`
- **Password**: `demo123`

## 🐛 Troubleshooting

### Problemi di Connessione Database
```bash
# Verifica lo stato del container PostgreSQL
docker-compose ps

# Controlla i log
docker-compose logs postgres
```

### Aggiornamento Mappature GICS
```bash
# Forza l'aggiornamento delle mappature
docker exec -it dollarpunk-app python init_gics_data.py
```

### Reset Database
```bash
# Rimuovi i volumi e ricrea tutto
docker-compose down -v
docker-compose up --build
```

## 📝 Note

- L'applicazione attende automaticamente che PostgreSQL sia pronto
- Le mappature GICS sono basate sulla classificazione ufficiale
- XOM è correttamente classificato come "Energy" ✅
- Supporto per titoli USA, Europa, UK, Svizzera
