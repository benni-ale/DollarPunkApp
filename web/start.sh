#!/bin/bash

echo "🚀 Avvio DollarPunk Web Application..."
echo ""

# Aspetta che PostgreSQL sia pronto (con timeout)
echo "⏳ Attendo che PostgreSQL sia pronto..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if python -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv('../.env')

try:
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'dollarpunk'),
        user=os.getenv('POSTGRES_USER', 'dollarpunk_user'),
        password=os.getenv('POSTGRES_PASSWORD', 'dollarpunk_password'),
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        connect_timeout=5
    )
    conn.close()
    print('✅ PostgreSQL pronto!')
    exit(0)
except Exception as e:
    print(f'❌ Tentativo {attempt + 1}: PostgreSQL non ancora pronto')
    exit(1)
" 2>/dev/null; then
        break
    fi
    
    attempt=$((attempt + 1))
    echo "⏳ Tentativo $attempt/$max_attempts..."
    sleep 3
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Timeout: PostgreSQL non è diventato disponibile dopo $max_attempts tentativi"
    echo "🚀 Avvio comunque l'applicazione..."
fi

echo ""
echo "🗄️ Database PostgreSQL connesso con successo!"
echo ""

echo "🔄 Esecuzione migrazione database..."
if [ -f "migrate_add_asset_type.py" ]; then
    python migrate_add_asset_type.py
    if [ $? -eq 0 ]; then
        echo "✅ Migrazione completata con successo!"
    else
        echo "❌ Errore durante la migrazione!"
    fi
else
    echo "⚠️  Script di migrazione non trovato, saltando..."
fi
echo ""

echo "🔧 Verifica configurazione Alpha Vantage..."

# Verifica semplice della chiave API
if python -c "
import os
from dotenv import load_dotenv
load_dotenv('../.env')
api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
if api_key:
    print('✅ ALPHA_VANTAGE_API_KEY trovata')
    exit(0)
else:
    print('❌ ALPHA_VANTAGE_API_KEY non trovata')
    exit(1)
" 2>/dev/null; then
    echo ""
    echo "🚀 Avvio server Flask..."
    echo "👤 Credenziali demo: demo@dollarpunk.com / demo123"
    echo "🌐 Applicazione disponibile su: http://localhost:5000"
    echo ""
    
    # Avvia l'applicazione Flask
    exec python app.py
else
    echo ""
    echo "❌ Errore nella configurazione. Controlla il file .env"
    exit 1
fi
