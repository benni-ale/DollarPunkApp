from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
import requests
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from functools import wraps
from database import init_db, get_user_by_email, verify_user_password, get_user_portfolio, add_portfolio_position, remove_portfolio_position, update_portfolio_position

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

def get_stock_name(symbol):
    """Restituisce il nome del titolo dato il simbolo"""
    names = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corp.',
        'NVDA': 'NVIDIA Corp.',
        'TSLA': 'Tesla Inc.',
        'ENEL.MI': 'Enel S.p.A.',
        'GOOGL': 'Alphabet Inc.',
        'AMZN': 'Amazon.com Inc.',
        'META': 'Meta Platforms Inc.',
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
        'EXO.MI': 'Exor N.V.'
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

def get_portfolio_data(user_email):
    """Calcola i dati del portafoglio per un utente specifico"""
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
                "positions_count": 0
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
            current_value = quote["price"] * position["quantity"]
            cost_basis = position["avg_price"] * position["quantity"]
            gain_loss = current_value - cost_basis
            gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0
            
            portfolio_data.append({
                "symbol": symbol,
                "quantity": position["quantity"],
                "avg_price": position["avg_price"],
                "current_price": quote["price"],
                "current_value": current_value,
                "cost_basis": cost_basis,
                "gain_loss": gain_loss,
                "gain_loss_percent": gain_loss_percent,
                "change_today": quote["change"],
                "change_percent_today": quote["change_percent"]
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
            "positions_count": len(portfolio_data)
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

@app.route('/api/portfolio')
@login_required
def api_portfolio():
    """API endpoint per i dati del portafoglio"""
    try:
        user_email = session['user_email']
        user_id = session.get('user_id')
        
        # Se è un utente demo (senza ID nel database), restituisci portafoglio vuoto
        if user_id is None:
            return jsonify({
                "positions": [],
                "summary": {
                    "total_value": 0,
                    "total_cost": 0,
                    "total_gain": 0,
                    "total_gain_percent": 0,
                    "positions_count": 0
                }
            })
        
        portfolio = get_portfolio_data(user_email)
        if portfolio:
            return jsonify(portfolio)
        else:
            return jsonify({"error": "Portafoglio non trovato"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        symbol = data.get('symbol', '').upper().strip()
        
        if not symbol:
            return jsonify({"error": "Simbolo non specificato"}), 400
        
        # Rimuovi la posizione dal database
        success, message = remove_portfolio_position(user_id, symbol)
        
        if success:
            return jsonify({"success": True, "message": f"Posizione {symbol} rimossa con successo"})
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
        
        symbol = data.get('symbol', '').upper().strip()
        quantity = float(data.get('quantity', 0))
        purchase_date = data.get('purchase_date', '')
        
        if not symbol or quantity <= 0 or not purchase_date:
            return jsonify({"error": "Dati non validi"}), 400
        
        # Ottieni il prezzo di chiusura alla data di acquisto
        historical_price = get_historical_price(symbol, purchase_date)
        if not historical_price:
            return jsonify({"error": f"Impossibile ottenere il prezzo storico per {symbol} alla data {purchase_date}"}), 404
        
        # Aggiorna la posizione nel database
        success, message = update_portfolio_position(
            user_id, symbol, quantity, purchase_date, historical_price
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
