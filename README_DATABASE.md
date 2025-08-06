# DollarPunk Database Integration

## 🗄️ Overview

DollarPunk ora supporta l'integrazione con database MySQL per storage persistente e idempotente dei dati. La GUI è stata trasformata da un semplice strumento di test a un'interfaccia completa per la gestione dei dati.

## 🚀 Features

### ✅ **Storage Idempotente**
- I dati vengono salvati nel database MySQL
- Operazioni `INSERT ... ON DUPLICATE KEY UPDATE` per evitare duplicati
- Gestione automatica delle sessioni di raccolta

### 📊 **Statistiche in Tempo Reale**
- Conteggio totale dei data points
- Statistiche giornaliere
- Distribuzione per piattaforma
- Sentiment score medio

### 🔄 **Gestione Sessioni**
- Creazione di sessioni di raccolta dati
- Tracking dello stato delle sessioni
- Log delle query Alpha Vantage

### 💾 **Persistenza Dati**
- Tutti i dati vengono salvati permanentemente
- Backup automatico tramite database
- Query e filtri avanzati

## 🛠️ Setup

### 1. **Installare MySQL**
```bash
# Ubuntu/Debian
sudo apt install mysql-server

# macOS
brew install mysql

# Windows
# Scarica MySQL Installer da https://dev.mysql.com/downloads/installer/
```

### 2. **Configurare il Database**
```bash
# Accedi a MySQL come root
mysql -u root -p

# Esegui lo script di setup
source database_setup.sql
```

### 3. **Configurare l'Applicazione**
L'URL del database predefinito è:
```
mysql://dollarpunk_user:dollarpunk_password@localhost:3306/dollarpunk
```

## 🎯 **Come Usare la GUI**

### **Tab Database**
1. **Connetti al Database**: Inserisci l'URL del database e clicca "Connect"
2. **Visualizza Statistiche**: Clicca "Refresh Stats" per vedere le statistiche
3. **Carica Dati**: Usa "Load Recent Data" per caricare i dati più recenti
4. **Gestisci Sessioni**: Crea nuove sessioni di raccolta

### **Tab Alpha Vantage**
1. **Configura API Key**: Inserisci la tua chiave API di Alpha Vantage
2. **Testa Connessione**: Verifica che l'API funzioni
3. **Recupera Dati**: I dati vengono automaticamente salvati nel database
4. **Monitora**: Vedi quanti dati sono stati inseriti/aggiornati

## 📈 **Vantaggi del Sistema Database**

### **Rispetto alla Memoria**
- ✅ **Persistenza**: I dati non si perdono al riavvio
- ✅ **Scalabilità**: Gestisce milioni di record
- ✅ **Concorrenza**: Supporta accessi multipli
- ✅ **Backup**: Backup automatici del database
- ✅ **Query**: Ricerche e filtri avanzati

### **Idempotenza**
- ✅ **Nessun Duplicato**: `ON DUPLICATE KEY UPDATE`
- ✅ **Aggiornamenti**: I dati esistenti vengono aggiornati
- ✅ **Sicurezza**: Operazioni atomiche
- ✅ **Performance**: Indici ottimizzati

## 🔧 **Struttura del Database**

### **Tabelle Principali**

#### `data_points`
- **id**: Chiave primaria unica
- **content**: Contenuto del post/articolo
- **platform**: Piattaforma di origine
- **timestamp**: Data e ora
- **theme**: Tema categorizzato
- **author**: Autore
- **sentiment_score**: Score di sentiment (da Alpha Vantage)
- **engagement_metrics**: Likes, shares, comments, views

#### `collection_sessions`
- **id**: ID unico della sessione
- **name**: Nome della sessione
- **status**: Stato (running/completed/failed/cancelled)
- **total_points**: Numero di punti raccolti

#### `alpha_vantage_queries`
- **id**: ID unico della query
- **session_id**: Riferimento alla sessione
- **topics**: Topics cercati
- **points_retrieved**: Punti recuperati
- **status**: Stato della query

## 📊 **Esempi di Query**

### **Statistiche Generali**
```sql
SELECT COUNT(*) as total_points FROM data_points;
SELECT platform, COUNT(*) FROM data_points GROUP BY platform;
SELECT AVG(sentiment_score) FROM data_points WHERE sentiment_score IS NOT NULL;
```

### **Dati Recenti**
```sql
SELECT * FROM data_points 
WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY timestamp DESC;
```

### **Filtri per Piattaforma**
```sql
SELECT * FROM data_points 
WHERE platform = 'AlphaVantage' 
AND theme = 'Economy'
ORDER BY timestamp DESC;
```

## 🚀 **Prossimi Sviluppi**

- [ ] **Dashboard Avanzata**: Grafici e visualizzazioni
- [ ] **Export Automatico**: Export periodico dei dati
- [ ] **Notifiche**: Alert per nuovi dati
- [ ] **API REST**: Endpoint per accesso esterno
- [ ] **Backup Automatico**: Backup schedulati
- [ ] **Replica**: Database replicati per alta disponibilità

## 🔒 **Sicurezza**

- **API Key**: Hash delle chiavi API per sicurezza
- **Connessioni**: Pool di connessioni limitato
- **Indici**: Ottimizzazione delle performance
- **Backup**: Backup regolari consigliati

## 📝 **Note**

- Il database viene creato automaticamente al primo avvio
- Le tabelle vengono create automaticamente se non esistono
- Tutte le operazioni sono idempotenti e sicure
- La GUI mostra feedback in tempo reale delle operazioni

---

**DollarPunk Database Integration** - Trasforma la tua GUI in un sistema professionale di gestione dati! 🎯 