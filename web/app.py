from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
import os
import requests
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from functools import wraps

# Carica le variabili d'ambiente dal file .env nella root del progetto
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dollarpunk-secret-key-change-in-production')

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

# File per salvare i portafogli personalizzati
PORTFOLIO_FILE = "user_portfolios.json"

def load_user_portfolios():
    """Carica i portafogli personalizzati dal file"""
    try:
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Errore nel caricamento portafogli: {e}")
        return {}

def save_user_portfolios(portfolios):
    """Salva i portafogli personalizzati nel file"""
    try:
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(portfolios, f, indent=2)
        return True
    except Exception as e:
        print(f"Errore nel salvataggio portafogli: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

def get_portfolio_data(user_email):
    """Calcola i dati del portafoglio per un utente specifico"""
    # Prima controlla se l'utente ha un portafoglio personalizzato
    user_portfolios = load_user_portfolios()
    if user_email in user_portfolios:
        portfolio = user_portfolios[user_email]
    elif user_email in USERS:
        portfolio = USERS[user_email]["portfolio"]
    else:
        return None
        
    portfolio_data = []
    total_value = 0
    total_cost = 0
    total_gain = 0
    
    for symbol, position in portfolio.items():
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
        
        if email in USERS and USERS[email]['password'] == password:
            session['user_email'] = email
            session['user_name'] = USERS[email]['name']
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
        user_email = session['user_email']
        data = request.get_json()
        
        symbol = data.get('symbol', '').upper().strip()
        quantity = float(data.get('quantity', 0))
        avg_price = float(data.get('avg_price', 0))
        
        if not symbol or quantity <= 0 or avg_price <= 0:
            return jsonify({"error": "Dati non validi"}), 400
        
        # Verifica che il titolo esista
        quote = get_stock_quote(symbol)
        if not quote:
            return jsonify({"error": f"Titolo {symbol} non trovato"}), 404
        
        # Carica i portafogli esistenti
        user_portfolios = load_user_portfolios()
        
        # Inizializza il portafoglio dell'utente se non esiste
        if user_email not in user_portfolios:
            user_portfolios[user_email] = {}
        
        # Aggiungi o aggiorna la posizione
        user_portfolios[user_email][symbol] = {
            "quantity": quantity,
            "avg_price": avg_price
        }
        
        # Salva i portafogli
        if save_user_portfolios(user_portfolios):
            return jsonify({"success": True, "message": f"Posizione {symbol} aggiunta con successo"})
        else:
            return jsonify({"error": "Errore nel salvataggio"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/remove', methods=['POST'])
@login_required
def api_remove_position():
    """API endpoint per rimuovere una posizione dal portafoglio"""
    try:
        user_email = session['user_email']
        data = request.get_json()
        
        symbol = data.get('symbol', '').upper().strip()
        
        if not symbol:
            return jsonify({"error": "Simbolo non specificato"}), 400
        
        # Carica i portafogli esistenti
        user_portfolios = load_user_portfolios()
        
        if user_email not in user_portfolios or symbol not in user_portfolios[user_email]:
            return jsonify({"error": f"Posizione {symbol} non trovata"}), 404
        
        # Rimuovi la posizione
        del user_portfolios[user_email][symbol]
        
        # Salva i portafogli
        if save_user_portfolios(user_portfolios):
            return jsonify({"success": True, "message": f"Posizione {symbol} rimossa con successo"})
        else:
            return jsonify({"error": "Errore nel salvataggio"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/update', methods=['POST'])
@login_required
def api_update_position():
    """API endpoint per aggiornare una posizione esistente"""
    try:
        user_email = session['user_email']
        data = request.get_json()
        
        symbol = data.get('symbol', '').upper().strip()
        quantity = float(data.get('quantity', 0))
        avg_price = float(data.get('avg_price', 0))
        
        if not symbol or quantity <= 0 or avg_price <= 0:
            return jsonify({"error": "Dati non validi"}), 400
        
        # Carica i portafogli esistenti
        user_portfolios = load_user_portfolios()
        
        if user_email not in user_portfolios or symbol not in user_portfolios[user_email]:
            return jsonify({"error": f"Posizione {symbol} non trovata"}), 404
        
        # Aggiorna la posizione
        user_portfolios[user_email][symbol] = {
            "quantity": quantity,
            "avg_price": avg_price
        }
        
        # Salva i portafogli
        if save_user_portfolios(user_portfolios):
            return jsonify({"success": True, "message": f"Posizione {symbol} aggiornata con successo"})
        else:
            return jsonify({"error": "Errore nel salvataggio"}), 500
            
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
    if not query:
        return jsonify([])
    
    user_email = session['user_email']
    
    # Carica il portafoglio dell'utente
    user_portfolios = load_user_portfolios()
    if user_email in user_portfolios:
        portfolio = user_portfolios[user_email]
    elif user_email in USERS:
        portfolio = USERS[user_email]["portfolio"]
    else:
        portfolio = {}
    
    # Restituisce titoli dal portafoglio dell'utente che corrispondono alla query
    results = []
    for symbol in portfolio.keys():
        if query in symbol:
            results.append({"symbol": symbol, "name": f"{symbol} Stock"})
    
    return jsonify(results)

if __name__ == '__main__':
    if not ALPHA_VANTAGE_API_KEY:
        print("❌ ERRORE: ALPHA_VANTAGE_API_KEY non trovata nelle variabili d'ambiente")
        print("Aggiungi ALPHA_VANTAGE_API_KEY=your_key al file .env")
        exit(1)
    
    print("✅ ALPHA_VANTAGE_API_KEY trovata")
    print("🚀 Avvio server Flask...")
    print("👤 Credenziali demo: demo@dollarpunk.com / demo123")
    app.run(debug=True, host='0.0.0.0', port=5000)
