from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
import requests
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from functools import wraps
from database import init_db, get_user_by_email, verify_user_password, get_user_portfolio, add_portfolio_position, remove_portfolio_position, update_portfolio_position
from models import PortfolioPosition

# Carica le variabili d'ambiente dal file .env nella root del progetto
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dollarpunk-secret-key-change-in-production')

# Configurazione database PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://dollarpunk_user:dollarpunk_password@postgres:5432/dollarpunk')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurazione Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Database utenti di esempio (in produzione usare un database reale)
USERS = {
    "demo@dollarpunk.com": {
        "password": "demo123",
        "name": "Demo User",
        "portfolio": {
            "AAPL": {"quantity": 25, "avg_price": 180.00},
            "MSFT": {"quantity": 15, "avg_price": 350.00},
            "NVDA": {"quantity": 8, "avg_price": 480.00},
            "TSLA": {"quantity": 10, "avg_price": 220.00},
            "ENEL.MI": {"quantity": 500, "avg_price": 6.50},
            "GOOGL": {"quantity": 5, "avg_price": 140.00},
            "AMZN": {"quantity": 12, "avg_price": 130.00},
            "META": {"quantity": 8, "avg_price": 280.00}
        }
    }
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            # Per le API, restituisci un errore JSON invece di un redirect
            if request.path.startswith('/api/'):
                return jsonify({"error": "Non autenticato"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_stock_currency(symbol):
    """Determina la valuta locale di un titolo"""
    # Titoli USA (NYSE, NASDAQ)
    us_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'ACN']
    
    # Titoli italiani (Borsa Italiana)
    it_stocks = ['ENEL.MI', 'ENI.MI', 'ISP.MI', 'UCG.MI', 'TIT.MI', 'STM.MI', 'PRY.MI', 'DIA.MI', 'SPM.MI', 'TEN.MI', 'RACE.MI', 'CNHI.MI', 'EXO.MI']
    
    if symbol in us_stocks:
        return 'USD'
    elif symbol in it_stocks:
        return 'EUR'
    else:
        # Default: assumi USD per titoli sconosciuti
        return 'USD'

def get_stock_region(symbol):
    """Determina l'area geografica di un titolo"""
    # Titoli USA
    us_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'ACN']
    
    # Titoli UK
    uk_stocks = ['HSBC', 'BP', 'GSK', 'VOD', 'RIO', 'BHP', 'ULVR', 'DGE']
    
    # Titoli francesi
    fr_stocks = ['OR.PA', 'MC.PA', 'ASML', 'TOT.PA', 'BNP.PA', 'CRH.PA', 'AIR.PA', 'CAP.PA']
    
    # Titoli tedeschi
    de_stocks = ['SAP.DE', 'SIE.DE', 'BMW.DE', 'DAI.DE', 'BAYN.DE', 'BAS.DE', 'ADS.DE', 'DTE.DE']
    
    # Titoli italiani
    it_stocks = ['ENEL.MI', 'ENI.MI', 'ISP.MI', 'UCG.MI', 'TIT.MI', 'STM.MI', 'PRY.MI', 'DIA.MI', 'SPM.MI', 'TEN.MI', 'RACE.MI', 'CNHI.MI', 'EXO.MI']
    
    # Titoli svizzeri
    ch_stocks = ['NOVN.SW', 'ROG.SW', 'NESN.SW', 'UBSG.SW', 'CSGN.SW', 'ABBN.SW']
    
    if symbol in us_stocks:
        return 'USA'
    elif symbol in uk_stocks:
        return 'UK'
    elif symbol in fr_stocks:
        return 'Francia'
    elif symbol in de_stocks:
        return 'Germania'
    elif symbol in it_stocks:
        return 'Italia'
    elif symbol in ch_stocks:
        return 'Svizzera'
    else:
        # Default: assumi USA per titoli sconosciuti
        return 'USA'

def get_stock_sector(symbol):
    """Determina il settore GICS di un titolo (livello più alto)"""
    # Information Technology (GICS 45)
    info_tech = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'ASML', 'SAP.DE', 'STM.MI', 'ACN', 'CAP.PA']
    
    # Consumer Discretionary (GICS 25)
    consumer_disc = ['AMZN', 'TSLA', 'OR.PA', 'MC.PA', 'BMW.DE', 'DAI.DE', 'RACE.MI', 'ADS.DE']
    
    # Energy (GICS 10)
    energy = ['BP', 'TOT.PA', 'ENI.MI', 'SPM.MI']
    
    # Financials (GICS 40)
    financials = ['HSBC', 'BNP.PA', 'UBSG.SW', 'CSGN.SW', 'ISP.MI', 'UCG.MI']
    
    # Health Care (GICS 35)
    health_care = ['GSK', 'ROG.SW', 'NOVN.SW', 'BAYN.DE', 'DIA.MI']
    
    # Industrials (GICS 20)
    industrials = ['SIE.DE', 'AIR.PA', 'ABBN.SW', 'CNHI.MI', 'TEN.MI']
    
    # Materials (GICS 15)
    materials = ['RIO', 'BHP', 'CRH.PA', 'BAS.DE', 'PRY.MI']
    
    # Consumer Staples (GICS 30)
    consumer_staples = ['ULVR', 'DGE', 'NESN.SW']
    
    # Utilities (GICS 55)
    utilities = ['ENEL.MI']
    
    # Communication Services (GICS 50)
    communication = ['VOD', 'TIT.MI', 'DTE.DE']
    
    # Real Estate (GICS 60)
    real_estate = []
    
    if symbol in info_tech:
        return 'Information Technology'
    elif symbol in consumer_disc:
        return 'Consumer Discretionary'
    elif symbol in energy:
        return 'Energy'
    elif symbol in financials:
        return 'Financials'
    elif symbol in health_care:
        return 'Health Care'
    elif symbol in industrials:
        return 'Industrials'
    elif symbol in materials:
        return 'Materials'
    elif symbol in consumer_staples:
        return 'Consumer Staples'
    elif symbol in utilities:
        return 'Utilities'
    elif symbol in communication:
        return 'Communication Services'
    elif symbol in real_estate:
        return 'Real Estate'
    else:
        return 'Other'

def get_stock_name(symbol):
    """Restituisce il nome del titolo dato il simbolo"""
    names = {
        # USA
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corp.',
        'GOOGL': 'Alphabet Inc.',
        'AMZN': 'Amazon.com Inc.',
        'TSLA': 'Tesla Inc.',
        'NVDA': 'NVIDIA Corp.',
        'META': 'Meta Platforms Inc.',
        'ACN': 'Accenture plc',
        
        # UK
        'HSBC': 'HSBC Holdings plc',
        'BP': 'BP plc',
        'GSK': 'GlaxoSmithKline plc',
        'VOD': 'Vodafone Group plc',
        'RIO': 'Rio Tinto Group',
        'BHP': 'BHP Group Ltd',
        'ULVR': 'Unilever plc',
        'DGE': 'Diageo plc',
        
        # Francia
        'OR.PA': 'L\'Oréal S.A.',
        'MC.PA': 'LVMH Moët Hennessy Louis Vuitton',
        'ASML': 'ASML Holding N.V.',
        'TOT.PA': 'TotalEnergies SE',
        'BNP.PA': 'BNP Paribas S.A.',
        'CRH.PA': 'Crédit Agricole S.A.',
        'AIR.PA': 'Airbus SE',
        'CAP.PA': 'Capgemini SE',
        
        # Germania
        'SAP.DE': 'SAP SE',
        'SIE.DE': 'Siemens AG',
        'BMW.DE': 'BMW AG',
        'DAI.DE': 'Daimler AG',
        'BAYN.DE': 'Bayer AG',
        'BAS.DE': 'BASF SE',
        'ADS.DE': 'Adidas AG',
        'DTE.DE': 'Deutsche Telekom AG',
        
        # Italia
        'ENEL.MI': 'Enel S.p.A.',
        'ENI.MI': 'Eni S.p.A.',
        'ISP.MI': 'Intesa Sanpaolo S.p.A.',
        'UCG.MI': 'UniCredit S.p.A.',
        'TIT.MI': 'Telecom Italia S.p.A.',
        'STM.MI': 'STMicroelectronics N.V.',
        'PRY.MI': 'Prysmian S.p.A.',
        'DIA.MI': 'DiaSorin S.p.A.',
        'SPM.MI': 'Saipem S.p.A.',
        'TEN.MI': 'Tenaris S.A.',
        'RACE.MI': 'Ferrari N.V.',
        'CNHI.MI': 'CNH Industrial N.V.',
        'EXO.MI': 'Exor N.V.',
        
        # Svizzera
        'NOVN.SW': 'Novartis AG',
        'ROG.SW': 'Roche Holding AG',
        'NESN.SW': 'Nestlé S.A.',
        'UBSG.SW': 'UBS Group AG',
        'CSGN.SW': 'Credit Suisse Group AG',
        'ABBN.SW': 'ABB Ltd'
    }
    return names.get(symbol, f"{symbol} Stock")

def get_stock_quote(symbol):
    """Ottiene il prezzo corrente di un titolo"""
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "symbol": symbol,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                "volume": int(quote.get("06. volume", 0)),
                "previous_close": float(quote.get("08. previous close", 0))
            }
        else:
            print(f"Errore per {symbol}: {data}")
            return None
            
    except Exception as e:
        print(f"Errore nell'ottenere quote per {symbol}: {e}")
        return None

def get_historical_price(symbol, date):
    """Ottiene il prezzo di chiusura storico per una data specifica"""
    try:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            
            # Cerca la data esatta
            if date in time_series:
                close_price = float(time_series[date]["4. close"])
                print(f"Prezzo trovato per {symbol} alla data {date}: €{close_price}")
                return close_price
            else:
                # Se la data non esiste (weekend/holiday), cerca la data più vicina precedente
                available_dates = sorted(time_series.keys(), reverse=True)
                
                # Prima cerca una data precedente
                for available_date in available_dates:
                    if available_date <= date:
                        close_price = float(time_series[available_date]["4. close"])
                        print(f"Usando prezzo del {available_date} per {symbol} (data richiesta: {date}): €{close_price}")
                        return close_price
                
                # Se non trova date precedenti, cerca la data più vicina successiva
                for available_date in available_dates:
                    if available_date >= date:
                        close_price = float(time_series[available_date]["4. close"])
                        print(f"Usando prezzo del {available_date} per {symbol} (data richiesta: {date}): €{close_price}")
                        return close_price
                
                print(f"Nessun dato storico trovato per {symbol} alla data {date}")
                return None
        else:
            # Controlla se c'è un errore di API
            if "Error Message" in data:
                print(f"Errore API Alpha Vantage per {symbol}: {data['Error Message']}")
            elif "Note" in data:
                print(f"Nota API Alpha Vantage per {symbol}: {data['Note']}")
            else:
                print(f"Errore sconosciuto per {symbol}: {data}")
            return None
            
    except Exception as e:
        print(f"Errore nell'ottenere prezzo storico per {symbol} alla data {date}: {e}")
        return None

# Cache per i tassi di cambio (per evitare troppe chiamate API)
exchange_rates_cache = {}
exchange_rates_cache_time = {}

def get_exchange_rate(from_currency, to_currency, date=None):
    """Ottiene il tasso di cambio tra due valute per una data specifica"""
    cache_key = f"{from_currency}_{to_currency}_{date or 'current'}"
    current_time = time.time()
    
    # Controlla se abbiamo un tasso in cache valido (max 1 ora per tassi correnti, 24 ore per storici)
    cache_duration = 3600 if date is None else 86400
    if (cache_key in exchange_rates_cache and 
        current_time - exchange_rates_cache_time.get(cache_key, 0) < cache_duration):
        return exchange_rates_cache[cache_key]
    
    try:
        if date is None:
            # Tasso corrente
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
        else:
            # Tasso storico
            params = {
                "function": "FX_DAILY",
                "from_symbol": from_currency,
                "to_symbol": to_currency,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
        
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if date is None:
            # Tasso corrente
            if "Realtime Currency Exchange Rate" in data:
                rate_info = data["Realtime Currency Exchange Rate"]
                rate = float(rate_info["5. Exchange Rate"])
            else:
                print(f"Errore nel tasso di cambio corrente {from_currency}->{to_currency}: {data}")
                return None
        else:
            # Tasso storico
            if "Time Series FX (Daily)" in data:
                time_series = data["Time Series FX (Daily)"]
                
                # Cerca la data esatta
                if date in time_series:
                    rate = float(time_series[date]["4. close"])
                else:
                    # Se la data non esiste, cerca la data più vicina precedente
                    available_dates = sorted(time_series.keys(), reverse=True)
                    
                    for available_date in available_dates:
                        if available_date <= date:
                            rate = float(time_series[available_date]["4. close"])
                            break
                    else:
                        # Se non trova date precedenti, usa il tasso più recente
                        if available_dates:
                            rate = float(time_series[available_dates[0]]["4. close"])
                        else:
                            print(f"Nessun dato storico trovato per {from_currency}->{to_currency} alla data {date}")
                            return None
            else:
                print(f"Errore nel tasso di cambio storico {from_currency}->{to_currency}: {data}")
                return None
        
        # Salva in cache
        exchange_rates_cache[cache_key] = rate
        exchange_rates_cache_time[cache_key] = current_time
        
        return rate
        
    except Exception as e:
        print(f"Errore nell'ottenere tasso di cambio {from_currency}->{to_currency}: {e}")
        return None

def get_portfolio_data(user_email, target_currency='EUR'):
    """Calcola i dati del portafoglio per un utente specifico con conversione valuta"""
    # Ottieni l'utente dal database
    user = get_user_by_email(user_email)
    if not user:
        return None
    
    # Ottieni le posizioni dal database
    portfolio_positions = get_user_portfolio(user.id)
    
    # Se non ci sono posizioni personalizzate, restituisci portafoglio vuoto
    if not portfolio_positions:
        return {
            "positions": [],
            "summary": {
                "total_value": 0,
                "total_cost": 0,
                "total_gain": 0,
                "total_gain_percent": 0,
                "positions_count": 0,
                "currency": target_currency
            }
        }
    
    portfolio_data = []
    total_value = 0
    total_cost = 0
    total_gain = 0
    
    for position in portfolio_positions:
        symbol = position["symbol"]
        quote = get_stock_quote(symbol)
        if quote:
            # Ottieni la valuta locale del titolo
            stock_currency = get_stock_currency(symbol)
            purchase_date = position["purchase_date"]
            
            # Prezzi in valuta locale (senza conversione)
            local_current_price = quote["price"]  # Prezzo corrente in valuta locale
            local_avg_price = position["avg_price"]  # Prezzo di acquisto in valuta locale
            
            # Calcola il controvalore nella valuta selezionata dall'utente
            if stock_currency != target_currency:
                # Tasso di cambio corrente per convertire dalla valuta locale alla valuta target
                exchange_rate = get_exchange_rate(stock_currency, target_currency) or 1.0
                current_value = local_current_price * position["quantity"] * exchange_rate
                cost_basis = local_avg_price * position["quantity"] * exchange_rate
            else:
                # Stessa valuta, nessuna conversione
                current_value = local_current_price * position["quantity"]
                cost_basis = local_avg_price * position["quantity"]
            
            gain_loss = current_value - cost_basis
            gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            portfolio_data.append({
                "id": position["id"],
                "symbol": symbol,
                "quantity": position["quantity"],
                "local_avg_price": local_avg_price,  # Prezzo carico in valuta locale
                "local_current_price": local_current_price,  # Prezzo corrente in valuta locale
                "current_value": current_value,  # Controvalore in valuta selezionata
                "cost_basis": cost_basis,
                "gain_loss": gain_loss,
                "gain_loss_percent": gain_loss_percent,
                "purchase_date": purchase_date,
                "stock_currency": stock_currency,  # Valuta locale del titolo
                "target_currency": target_currency,  # Valuta selezionata dall'utente
                "region": get_stock_region(symbol),  # Area geografica
                "sector": get_stock_sector(symbol)  # Settore GICS
            })
            
            total_value += current_value
            total_cost += cost_basis
            total_gain += gain_loss
        
        # Rate limiting per Alpha Vantage (5 calls per minuto per free tier)
        time.sleep(0.2)
    
    return {
        "positions": portfolio_data,
        "summary": {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain": total_gain,
            "total_gain_percent": (total_gain / total_cost * 100) if total_cost > 0 else 0,
            "positions_count": len(portfolio_data),
            "currency": target_currency
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/portfolio')
def portfolio():
    if 'user_email' in session:
        return render_template('portfolio-software.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Prima prova con il database
        user = get_user_by_email(email)
        if user and verify_user_password(user, password):
            session['user_email'] = email
            session['user_name'] = user.name
            session['user_id'] = user.id
            flash('Login effettuato con successo!', 'success')
            return redirect(url_for('dashboard'))
        
        # Fallback per utenti demo
        elif email in USERS and USERS[email]['password'] == password:
            session['user_email'] = email
            session['user_name'] = USERS[email]['name']
            session['user_id'] = None  # Utente demo
            flash('Login effettuato con successo!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email o password non validi', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('portfolio-software.html')

@app.route('/api/portfolio', methods=['GET'])
@login_required
def api_portfolio():
    """API endpoint per i dati del portafoglio con supporto valuta"""
    try:
        user_email = session['user_email']
        user_id = session.get('user_id')
        currency = request.args.get('currency', 'EUR')
        
        # Se è un utente demo (senza ID nel database), restituisci portafoglio vuoto
        if user_id is None:
            return jsonify({
                "positions": [],
                "summary": {
                    "total_value": 0,
                    "total_cost": 0,
                    "total_gain": 0,
                    "total_gain_percent": 0,
                    "positions_count": 0,
                    "currency": currency
                }
            })
        
        portfolio = get_portfolio_data(user_email, currency)
        if portfolio:
            return jsonify(portfolio)
        else:
            return jsonify({"error": "Portafoglio non trovato"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/exchange-rates', methods=['GET'])
@login_required
def get_exchange_rates():
    """Endpoint per ottenere tutti i tassi di cambio supportati"""
    base_currency = request.args.get('base', 'EUR')
    supported_currencies = ['EUR', 'USD', 'INR', 'GBP', 'CAD', 'AUD', 'NZD', 'HKD', 'SGD']
    
    rates = {}
    for currency in supported_currencies:
        if currency != base_currency:
            rate = get_exchange_rate(base_currency, currency)
            if rate:
                rates[currency] = rate
    
    return jsonify({
        "base_currency": base_currency,
        "rates": rates,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/currency-info', methods=['GET'])
@login_required
def get_currency_info():
    """Endpoint per ottenere informazioni sui tassi di cambio con performance"""
    base_currency = 'EUR'
    supported_currencies = ['USD', 'INR', 'GBP', 'CAD', 'AUD', 'NZD', 'HKD', 'SGD']
    
    currency_info = []
    
    for currency in supported_currencies:
        current_rate = get_exchange_rate(base_currency, currency)
        
        # Calcola il tasso di cambio di una settimana fa per la performance
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        week_ago_rate = get_exchange_rate(base_currency, currency, week_ago)
        
        if current_rate and week_ago_rate:
            change_percent = ((current_rate - week_ago_rate) / week_ago_rate) * 100
            
            currency_info.append({
                'currency': currency,
                'rate': current_rate,
                'change_percent': change_percent,
                'week_ago_rate': week_ago_rate
            })
    
    return jsonify({
        'base_currency': base_currency,
        'currencies': currency_info,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/portfolio/add', methods=['POST'])
@login_required
def api_add_position():
    """API endpoint per aggiungere una posizione al portafoglio"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Utente demo non può aggiungere posizioni personalizzate"}), 403
        
        data = request.get_json()
        
        symbol = data.get('symbol', '').upper().strip()
        quantity = float(data.get('quantity', 0))
        purchase_date = data.get('purchase_date', '')
        
        if not symbol or quantity <= 0 or not purchase_date:
            return jsonify({"error": "Dati non validi"}), 400
        
        # Verifica che il titolo esista
        quote = get_stock_quote(symbol)
        if not quote:
            return jsonify({"error": f"Titolo {symbol} non trovato"}), 404
        
        # Ottieni il prezzo di chiusura alla data di acquisto
        historical_price = get_historical_price(symbol, purchase_date)
        if not historical_price:
            return jsonify({"error": f"Impossibile ottenere il prezzo storico per {symbol} alla data {purchase_date}"}), 404
        
        # Aggiungi la posizione al database
        success, message = add_portfolio_position(
            user_id, symbol, quantity, purchase_date, historical_price
        )
        
        if success:
            return jsonify({
                "success": True, 
                "message": f"Posizione {symbol} aggiunta con successo al prezzo di €{historical_price:.2f} del {purchase_date}"
            })
        else:
            return jsonify({"error": message}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/remove', methods=['POST'])
@login_required
def api_remove_position():
    """API endpoint per rimuovere una posizione dal portafoglio"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Utente demo non può rimuovere posizioni personalizzate"}), 403
        
        data = request.get_json()
        
        position_id = data.get('position_id')
        
        if not position_id:
            return jsonify({"error": "ID posizione non specificato"}), 400
        
        # Rimuovi la posizione dal database
        success, message = remove_portfolio_position(user_id, position_id)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"error": message}), 404 if "non trovata" in message else 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/update', methods=['POST'])
@login_required
def api_update_position():
    """API endpoint per aggiornare una posizione esistente"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Utente demo non può aggiornare posizioni personalizzate"}), 403
        
        data = request.get_json()
        
        position_id = data.get('position_id')
        quantity = float(data.get('quantity', 0))
        purchase_date = data.get('purchase_date', '')
        
        if not position_id or quantity <= 0 or not purchase_date:
            return jsonify({"error": "Dati non validi"}), 400
        
        # Ottieni il simbolo dalla posizione esistente
        position = PortfolioPosition.query.filter_by(user_id=user_id, id=position_id).first()
        if not position:
            return jsonify({"error": "Posizione non trovata"}), 404
        
        symbol = position.symbol
        
        # Ottieni il prezzo di chiusura alla data di acquisto
        historical_price = get_historical_price(symbol, purchase_date)
        if not historical_price:
            return jsonify({"error": f"Impossibile ottenere il prezzo storico per {symbol} alla data {purchase_date}"}), 404
        
        # Aggiorna la posizione nel database
        success, message = update_portfolio_position(
            user_id, position_id, quantity, purchase_date, historical_price
        )
        
        if success:
            return jsonify({
                "success": True, 
                "message": f"Posizione {symbol} aggiornata con successo al prezzo di €{historical_price:.2f} del {purchase_date}"
            })
        else:
            return jsonify({"error": message}), 404 if "non trovata" in message else 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<symbol>')
@login_required
def api_stock(symbol):
    """API endpoint per i dati di un singolo titolo"""
    try:
        quote = get_stock_quote(symbol)
        if quote:
            return jsonify(quote)
        else:
            return jsonify({"error": "Titolo non trovato"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search')
@login_required
def api_search():
    """API endpoint per cercare titoli"""
    query = request.args.get('q', '').upper()
    if len(query) < 2:
        return jsonify([])
    
    # Search in user's portfolio first
    user_portfolios = load_user_portfolios()
    user_email = session.get('user_email')
    user_portfolio = user_portfolios.get(user_email, {})
    
    results = []
    for symbol in user_portfolio.keys():
        if query in symbol:
            results.append({
                'symbol': symbol,
                'name': get_stock_name(symbol),
                'in_portfolio': True
            })
    
    # Also search in common stocks
    common_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'ENEL.MI', 'ENI.MI', 'ISP.MI']
    for symbol in common_stocks:
        if query in symbol and symbol not in [r['symbol'] for r in results]:
            results.append({
                'symbol': symbol,
                'name': get_stock_name(symbol),
                'in_portfolio': False
            })
    
    return jsonify(results[:10])  # Limit to 10 results

@app.route('/api/tickers')
@login_required
def api_tickers():
    """Return all available tickers for autocomplete"""
    try:
        # Read tickers from symbols.csv
        tickers = []
        symbols_file = os.path.join(os.path.dirname(__file__), 'symbols.csv')
        if os.path.exists(symbols_file):
            with open(symbols_file, 'r', encoding='utf-8') as f:
                next(f)  # Skip header
                for line in f:
                    ticker = line.strip()
                    if ticker:
                        tickers.append(ticker)
        return jsonify(tickers)
    except Exception as e:
        print(f"Error loading tickers: {e}")
        return jsonify([])

@app.route('/api/test')
def api_test():
    """Test endpoint to verify routing is working"""
    return jsonify({"message": "API is working", "endpoints": ["/api/portfolio/add", "/api/portfolio/remove", "/api/portfolio/update"]})

@app.route('/api/test-post', methods=['POST'])
def api_test_post():
    """Test POST endpoint to verify POST requests work"""
    data = request.get_json() or {}
    return jsonify({
        "message": "POST request received",
        "data": data,
        "method": request.method
    })

@app.route('/api/debug/routes')
def api_debug_routes():
    """Debug endpoint to see all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
    return jsonify(routes)

@app.route('/api/debug/session')
def api_debug_session():
    """Debug endpoint to check session status"""
    return jsonify({
        'authenticated': 'user_email' in session,
        'user_email': session.get('user_email'),
        'user_name': session.get('user_name'),
        'session_data': dict(session)
    })

@app.route('/api/debug/historical/<symbol>/<date>')
def api_debug_historical(symbol, date):
    """Debug endpoint to test historical price function"""
    try:
        price = get_historical_price(symbol, date)
        if price:
            return jsonify({
                'symbol': symbol,
                'date': date,
                'price': price,
                'success': True
            })
        else:
            return jsonify({
                'symbol': symbol,
                'date': date,
                'price': None,
                'success': False,
                'error': 'Prezzo non trovato'
            }), 404
    except Exception as e:
        return jsonify({
            'symbol': symbol,
            'date': date,
            'error': str(e),
            'success': False
        }), 500

if __name__ == '__main__':
    if not ALPHA_VANTAGE_API_KEY:
        print("❌ ERRORE: ALPHA_VANTAGE_API_KEY non trovata nelle variabili d'ambiente")
        print("Aggiungi ALPHA_VANTAGE_API_KEY=your_key al file .env")
        exit(1)
    
    print("✅ ALPHA_VANTAGE_API_KEY trovata")
    
    # Inizializza il database
    print("🗄️ Inizializzazione database PostgreSQL...")
    if init_db(app):
        print("✅ Database inizializzato con successo")
        print("🚀 Avvio server Flask...")
        print("👤 Credenziali demo: demo@dollarpunk.com / demo123")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Errore nell'inizializzazione del database")
        exit(1)
