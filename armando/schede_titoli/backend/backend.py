# app.py
import os, time, requests, csv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE = "https://www.alphavantage.co/query"

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

CACHE = {}  # {key: (timestamp, data)}
TTL = 60  # sec (metti 300–600 in prod)

# Load tickers from CSV
TICKERS = []
def load_tickers():
    global TICKERS
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'symbols.csv')
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            TICKERS = [row['symbol'] for row in reader]
        print(f"✅ Loaded {len(TICKERS)} tickers from CSV")
    except Exception as e:
        print(f"⚠️ Error loading tickers: {e}")
        # Fallback to common tickers
        TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA', 'JPM', 'V', 'ENI.MI', 'ENEL.MI', 'TIT.MI', 'ISP.MI']

# Load tickers on startup
load_tickers()

def av_call(params):
    params["apikey"] = API_KEY
    r = requests.get(BASE, params=params, timeout=15)
    j = r.json()
    if "Note" in j or "Information" in j:  # rate limit o key issue
        raise HTTPException(429, detail=j)
    if "Error Message" in j:
        raise HTTPException(400, detail=j["Error Message"])
    return j

def cached(key, fn):
    now = time.time()
    if key in CACHE and now - CACHE[key][0] < TTL:
        return CACHE[key][1]
    data = fn()
    CACHE[key] = (now, data)
    return data

@app.get("/api/tickers")
def get_tickers():
    """Get all available tickers"""
    return {"tickers": TICKERS}

@app.get("/api/search/{query}")
def search_tickers(query: str):
    """Search tickers by query"""
    query = query.upper()
    results = [ticker for ticker in TICKERS if query in ticker][:20]  # Limit to 20 results
    return {"results": results}

@app.get("/api/stock/{symbol}")
def stock(symbol: str):
    symbol = symbol.upper()

    # GLOBAL_QUOTE
    quote = cached(
        f"quote:{symbol}",
        lambda: av_call({"function": "GLOBAL_QUOTE", "symbol": symbol}).get("Global Quote", {})
    )

    # OVERVIEW (fundamentals)
    overview = cached(
        f"overview:{symbol}",
        lambda: av_call({"function": "OVERVIEW", "symbol": symbol})
    )

    # TIME SERIES (solo ultimi 200)
    series = cached(
        f"series:{symbol}",
        lambda: av_call({"function": "TIME_SERIES_DAILY_ADJUSTED", "symbol": symbol, "outputsize": "compact"})
    ).get("Time Series (Daily)", {})

    # normalizzazione minima per la scheda
    latest_date, latest = (next(iter(series.items())) if series else (None, None))
    price = float(quote.get("05. price", latest["4. close"]) ) if latest else None
    prev_close = float(quote.get("08. previous close", latest["5. adjusted close"]) ) if latest else None
    chg = (price - prev_close) if (price and prev_close) else None
    chg_pct = (chg / prev_close * 100) if (chg and prev_close) else None

    # time series per grafico (ordinata per data crescente)
    ts = [{"date": d, "close": float(v["4. close"])} for d, v in series.items()]
    ts = sorted(ts, key=lambda x: x["date"])

    return {
        "symbol": symbol,
        "name": overview.get("Name"),
        "sector": overview.get("Sector"),
        "currency": overview.get("Currency"),
        "marketCap": overview.get("MarketCapitalization"),
        "pe": overview.get("PERatio"),
        "beta": overview.get("Beta"),
        "dividendYield": overview.get("DividendYield"),
        "price": price,
        "prevClose": prev_close,
        "change": chg,
        "changePct": chg_pct,
        "asOf": latest_date,
        "timeseries": ts,
        "raw": {"quote": quote}  # utile per debug
    }
