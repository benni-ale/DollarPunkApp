FROM python:3.9-slim

WORKDIR /app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY . .

# Rendi eseguibile lo script di avvio
RUN chmod +x start.sh

# Esponi la porta
EXPOSE 5000

# Comando di avvio
CMD ["./start.sh"]
