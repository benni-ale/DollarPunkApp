FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file di requirements
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY process_news_data.py .

# Crea la directory di output se non esiste
RUN mkdir -p /app/output/processed

# Comando di default
CMD ["python", "process_news_data.py"]
