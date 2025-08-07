#!/bin/bash

echo "🧪 Test Alpha Vantage Integration with Database"
echo "================================================"

# Verifica che il file di configurazione esista
if [ ! -f "config_alpha_vantage.toml" ]; then
    echo "❌ File config_alpha_vantage.toml non trovato"
    echo "💡 Crea il file di configurazione prima di procedere"
    exit 1
fi

# Verifica che l'API key sia configurata
if grep -q "YOUR_ALPHA_VANTAGE_API_KEY_HERE" config_alpha_vantage.toml; then
    echo "⚠️  API key Alpha Vantage non configurata"
    echo "💡 Modifica config_alpha_vantage.toml e aggiungi la tua API key"
    echo ""
    echo "Esempio:"
    echo "api_key = \"demo\"  # Per test gratuiti"
    echo "api_key = \"your_real_api_key_here\"  # Per API key reale"
    exit 1
fi

echo "✅ Configurazione trovata"
echo ""

# Test 1: Validazione configurazione
echo "📋 Test 1: Validazione configurazione"
cargo run -- validate-config config_alpha_vantage.toml
echo ""

# Test 2: Test Alpha Vantage senza database
echo "📊 Test 2: Test Alpha Vantage (senza database)"
cargo run -- test-alpha-vantage --config config_alpha_vantage.toml
echo ""

# Test 3: Test Alpha Vantage con database (se disponibile)
echo "💾 Test 3: Test Alpha Vantage con database"
echo "💡 Assicurati che MySQL sia in esecuzione e il database 'dollarpunk' esista"
echo ""

# Chiedi conferma per il test con database
read -p "Vuoi testare con il database? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Avvio test con database..."
    cargo run -- test-alpha-vantage \
        --config config_alpha_vantage.toml \
        --database-url "mysql://root:password@localhost/dollarpunk" \
        --save-to-db
else
    echo "⏭️  Test con database saltato"
fi

echo ""
echo "✅ Test completati!"
echo ""
echo "📝 Prossimi passi:"
echo "1. Se hai un'API key reale, sostituiscila in config_alpha_vantage.toml"
echo "2. Configura il database MySQL se necessario"
echo "3. Esegui: cargo run -- collect-data --config config_alpha_vantage.toml --save-to-db" 