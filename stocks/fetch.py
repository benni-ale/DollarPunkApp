import os
import time
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **k): return x

# ============ CONFIG ============
print("🔧 Loading configuration...")
print(f"📁 Current working directory: {os.getcwd()}")
print(f"📁 Script location: {Path(__file__).resolve()}")

# Try to load .env file
env_path = find_dotenv()
print(f"🔍 Looking for .env file: {env_path}")
if env_path:
    print(f"✅ Found .env file at: {env_path}")
else:
    print("⚠️  No .env file found")

load_dotenv(find_dotenv())  # carica .env dalla root

# Debug environment variables
print("🔍 Environment variables:")
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
print(f"   ALPHA_VANTAGE_API_KEY: {'✅ Set' if API_KEY else '❌ Missing'}")

RAW_TICKERS = os.getenv("TICKERS", "")
print(f"   TICKERS: '{RAW_TICKERS}'")

if not API_KEY:
    print("❌ ERROR: Missing ALPHA_VANTAGE_API_KEY")
    raise RuntimeError("Missing ALPHA_VANTAGE_API_KEY")

TICKERS = [t.strip().upper() for t in RAW_TICKERS.split(",") if t.strip()]
print(f"   Parsed TICKERS: {TICKERS}")

if not TICKERS:
    print("❌ ERROR: No TICKERS provided")
    raise RuntimeError("No TICKERS provided")

MAX_TICKERS_PER_RUN = int(os.getenv("MAX_TICKERS_PER_RUN", "10"))
DAYS_TO_FETCH = int(os.getenv("DAYS_TO_FETCH", "365"))
SLEEP_BETWEEN_CALLS = int(os.getenv("SLEEP_BETWEEN_CALLS", "15"))  # 5 req/min piano free
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

print(f"   MAX_TICKERS_PER_RUN: {MAX_TICKERS_PER_RUN}")
print(f"   DAYS_TO_FETCH: {DAYS_TO_FETCH}")
print(f"   SLEEP_BETWEEN_CALLS: {SLEEP_BETWEEN_CALLS}")
print(f"   MAX_RETRIES: {MAX_RETRIES}")

# Output: /app/output/stocks (mounted from ../output)
OUTPUT_DIR = Path("/app/output/stocks")
print(f"📁 OUTPUT_DIR: {OUTPUT_DIR}")

try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created/verified output directory: {OUTPUT_DIR}")
except Exception as e:
    print(f"❌ Error creating output directory: {e}")
    raise

print("✅ Configuration loaded successfully!")
# ================================

def normalize_candidates(symbol: str):
    yield symbol
    if "-" in symbol:
        yield symbol.replace("-", ".")

def call_alpha_daily(symbol: str):
    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}"
        f"&outputsize=full&apikey={API_KEY}"
    )
    try:
        r = requests.get(url, timeout=30)
    except Exception as e:
        return None, f"http_error: {e}"
    if r.status_code != 200:
        return None, f"http_status_{r.status_code}"
    data = r.json()
    if "Note" in data:
        return None, "rate_limited"
    if "Error Message" in data or "Information" in data:
        return None, "api_error"
    ts = data.get("Time Series (Daily)")
    if not ts:
        return None, "no_timeseries"
    return ts, "ok"

def fetch_prices_for_symbol(symbol: str):
    last_status = None
    for candidate in normalize_candidates(symbol):
        ts, status = call_alpha_daily(candidate)
        if status == "ok":
            return ts, "ok", candidate
        if status == "rate_limited":
            return None, status, candidate
        last_status = status
    return None, last_status or "unknown_error", symbol

def parse_row(date_str, payload):
    return {
        "date": date_str,
        "open": payload.get("1. open"),
        "high": payload.get("2. high"),
        "low": payload.get("3. low"),
        "close": payload.get("4. close"),
        "volume": payload.get("6. volume") or payload.get("5. volume"),
    }

def load_existing_dates(csv_path: Path):
    if not csv_path.exists():
        return set()
    dates = set()
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = row.get("date")
            if d:
                dates.add(d)
    return dates

def write_rows(csv_path: Path, rows):
    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "open", "high", "low", "close", "volume"])
        if write_header:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)

def within_last_days(date_str, days):
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return d >= (datetime.utcnow().date() - timedelta(days=days))
    except Exception:
        return False

def fetch_historical_prices():
    print("\n" + "="*50)
    print("🚀 Starting OHLCV ingestion → output/stocks/")
    print("="*50)
    print(f"📅 Days: {DAYS_TO_FETCH} | Tickers: {len(TICKERS)} (max {MAX_TICKERS_PER_RUN})")
    print(f"🎯 Tickers to process: {TICKERS[:MAX_TICKERS_PER_RUN]}")
    total_new = total_skipped = processed = 0

    for idx, raw_symbol in enumerate(tqdm(TICKERS[:MAX_TICKERS_PER_RUN], desc="Tickers")):
        symbol = raw_symbol.strip().upper()
        csv_path = OUTPUT_DIR / f"{symbol}.csv"
        existing_dates = load_existing_dates(csv_path)

        retries = 0
        while True:
            ts, status, used_symbol = fetch_prices_for_symbol(symbol)
            if status == "ok":
                break
            if status == "rate_limited":
                retries += 1
                if retries > MAX_RETRIES:
                    print(f"⛔ Rate limit persistente per {symbol}, skip.")
                    ts = None
                    break
                sleep_s = max(15, SLEEP_BETWEEN_CALLS) * retries
                print(f"⏳ Rate limited {symbol}. Retry {retries}/{MAX_RETRIES} tra {sleep_s}s…")
                time.sleep(sleep_s)
                continue
            elif status in ("api_error", "no_timeseries"):
                print(f"🚫 API error/no data per {symbol} (var: {used_symbol}). Skip.")
                ts = None
                break
            else:
                print(f"❌ {symbol}: {status}. Skip.")
                ts = None
                break

        if not ts:
            if idx < min(len(TICKERS), MAX_TICKERS_PER_RUN) - 1:
                time.sleep(SLEEP_BETWEEN_CALLS)
            continue

        new_rows = []
        for d, payload in ts.items():
            if not within_last_days(d, DAYS_TO_FETCH):
                continue
            if d in existing_dates:
                total_skipped += 1
                continue
            row = parse_row(d, payload)
            if row["open"] and row["close"]:
                new_rows.append(row)

        new_rows.sort(key=lambda r: r["date"])

        if new_rows:
            write_rows(csv_path, new_rows)
            print(f"💾 {symbol}: +{len(new_rows)} (file: {csv_path})")
            total_new += len(new_rows)
        else:
            print(f"➡️  {symbol}: nessuna nuova riga")

        processed += 1
        if idx < min(len(TICKERS), MAX_TICKERS_PER_RUN) - 1:
            time.sleep(SLEEP_BETWEEN_CALLS)

    print("\n🎉 DONE")
    print(f"   • Processati: {processed}")
    print(f"   • Nuove righe: {total_new}")
    print(f"   • Duplicati: {total_skipped}")

if __name__ == "__main__":
    try:
        print("🎬 Starting stocks data fetcher...")
        fetch_historical_prices()
        print("🎉 Script completed successfully!")
    except Exception as e:
        print(f"💥 Script failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
