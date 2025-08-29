from flask import Flask, render_template, jsonify, request
import os
import requests
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env nella root del progetto
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

# Configurazione Alpha Vantage
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

# Portafoglio di esempio (può essere espanso)
SAMPLE_PORTFOLIO = {
    "AAPL": {"quantity": 25, "avg_price": 180.00},
    "MSFT": {"quantity": 15, "avg_price": 350.00},
    "NVDA": {"quantity": 8, "avg_price": 480.00},
    "TSLA": {"quantity": 10, "avg_price": 220.00},
    "ENEL.MI": {"quantity": 500, "avg_price": 6.50},
    "GOOGL": {"quantity": 5, "avg_price": 140.00},
    "AMZN": {"quantity": 12, "avg_price": 130.00},
    "META": {"quantity": 8, "avg_price": 280.00}
}

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

def get_portfolio_data():
    """Calcola i dati del portafoglio"""
    portfolio_data = []
    total_value = 0
    total_cost = 0
    total_gain = 0
    
    for symbol, position in SAMPLE_PORTFOLIO.items():
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
    return render_template('portfolio-software.html')

@app.route('/api/portfolio')
def api_portfolio():
    """API endpoint per i dati del portafoglio"""
    try:
        portfolio = get_portfolio_data()
        return jsonify(portfolio)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<symbol>')
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
def api_search():
    """API endpoint per cercare titoli"""
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify([])
    
    # Per ora restituisce solo titoli dal portafoglio di esempio
    # In futuro si può integrare con Alpha Vantage Search API
    results = []
    for symbol in SAMPLE_PORTFOLIO.keys():
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
    app.run(debug=True, host='0.0.0.0', port=5000)
