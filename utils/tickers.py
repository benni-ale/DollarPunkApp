import os
import requests
import csv
import json
from datetime import datetime
from dotenv import load_dotenv

# Carica la chiave API dal file .env
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

if not API_KEY:
    raise ValueError("ALPHA_VANTAGE_API_KEY non trovata nel file .env")

def download_listing_status():
    """Scarica il file completo di listing status da Alpha Vantage"""
    print("Inizio download listing status da Alpha Vantage...")
    print(f"API Key: {API_KEY[:8]}...")
    
    # URL di richiesta
    url = f"https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={API_KEY}"
    
    try:
        # Fare la richiesta per ottenere i dati
        print("Effettuo richiesta a Alpha Vantage...")
        response = requests.get(url)
        
        # Controlla la risposta
        if response.status_code == 200:
            # Crea timestamp per il nome del file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Assicurati che la directory output esista
            output_dir = "/app/output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Salva il contenuto della risposta in un file CSV con timestamp
            output_file = os.path.join(output_dir, f"listing_status_{timestamp}.csv")
            with open(output_file, "wb") as file:
                file.write(response.content)
            
            print(f"✓ Dati salvati in: {output_file}")
            print(f"✓ Dimensione file: {len(response.content)} bytes")
            
            return output_file, response.text
            
        else:
            print(f"✗ Errore nella richiesta: {response.status_code}")
            print(f"Risposta: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"✗ Errore durante il download: {e}")
        return None, None

def extract_symbols_and_names(csv_content):
    """Estrae solo symbol e name dal contenuto CSV"""
    print("\nEstraggo symbol e name...")
    
    symbols_and_names = []
    lines = csv_content.strip().split('\n')
    
    # Leggi l'header e puliscilo
    if lines:
        header = [col.strip().replace('\r', '') for col in lines[0].split(',')]
        print(f"Header trovato: {header}")
    
    # Debug: mostra le prime righe per capire il formato
    print(f"\nPrime 5 righe del file:")
    for i, line in enumerate(lines[1:6], 1):
        parts = [part.strip().replace('\r', '') for part in line.split(',')]
        if len(parts) >= 2:
            print(f"  {i}. {parts[0]} - {parts[1]}")
    
    # Processa ogni riga
    for i, line in enumerate(lines[1:], 1):  # Salta l'header
        if line.strip():  # Ignora righe vuote
            parts = [part.strip().replace('\r', '') for part in line.split(',')]
            if len(parts) >= 2:  # Almeno symbol e name devono essere presenti
                symbol = parts[0].strip()
                name = parts[1].strip()
                
                symbols_and_names.append({
                    'symbol': symbol,
                    'name': name
                })
    
    print(f"\nTicker totali estratti: {len(symbols_and_names)}")
    return symbols_and_names

def save_tickers_data(tickers_data, timestamp):
    """Salva i ticker in formato JSON e CSV"""
    output_dir = "/app/output"
    
    # Salva in JSON
    json_file = os.path.join(output_dir, f"tickers_{timestamp}.json")
    json_data = {
        'timestamp': timestamp,
        'source': 'Alpha Vantage Listing Status',
        'total_tickers': len(tickers_data),
        'tickers': tickers_data
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Ticker salvati in JSON: {json_file}")
    
    # Salva in CSV con symbol e name
    csv_file = os.path.join(output_dir, f"tickers_{timestamp}.csv")
    if tickers_data:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['symbol', 'name'])
            writer.writeheader()
            writer.writerows(tickers_data)
        
        print(f"✓ Ticker salvati in CSV: {csv_file}")
    
    # Salva in CSV con solo i simboli
    symbols_only_file = os.path.join(output_dir, f"symbols_{timestamp}.csv")
    if tickers_data:
        symbols = [ticker['symbol'] for ticker in tickers_data]
        with open(symbols_only_file, 'w', newline='', encoding='utf-8') as f:
            f.write('symbol\n')  # Header
            for symbol in symbols:
                f.write(f'{symbol}\n')
        
        print(f"✓ Simboli salvati in CSV: {symbols_only_file}")
    
    return json_file, csv_file, symbols_only_file

if __name__ == "__main__":
    # Download del listing status
    csv_file, csv_content = download_listing_status()
    
    if csv_content:
        # Estrai symbol e name
        tickers_data = extract_symbols_and_names(csv_content)
        
        if tickers_data:
            # Salva i risultati
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file, csv_file, symbols_only_file = save_tickers_data(tickers_data, timestamp)
            
            print(f"\n{'='*50}")
            print("RIEPILOGO:")
            print(f"✓ File completo scaricato: listing_status_{timestamp}.csv")
            print(f"✓ Ticker estratti: {len(tickers_data)}")
            print(f"✓ File JSON creato: tickers_{timestamp}.json")
            print(f"✓ File CSV creato: tickers_{timestamp}.csv")
            print(f"✓ File simboli creato: symbols_{timestamp}.csv")
            
            # Mostra alcuni esempi
            print(f"\nPrimi 10 ticker:")
            for i, ticker in enumerate(tickers_data[:10], 1):
                print(f"  {i}. {ticker['symbol']} - {ticker['name']}")
        else:
            print("✗ Nessun ticker estratto dal file")
    else:
        print("✗ Impossibile procedere senza il file di listing status")
