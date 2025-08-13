#!/usr/bin/env python3
"""
Script per processare i dati delle news JSON e creare tabelle separate per topics e tickers.
Deduplica per URL e crea due output distinti.
"""

import json
import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
import logging
from datetime import datetime
import hashlib

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsDataProcessor:
    def __init__(self, input_dir: str = "../output", output_dir: str = "../output/processed"):
        # Gestisce i percorsi sia per esecuzione locale che Docker
        if Path("/app").exists():
            # Siamo in Docker, usa percorsi assoluti
            self.input_dir = Path("/app/output")
            self.output_dir = Path("/app/output/processed")
        else:
            # Esecuzione locale
            self.input_dir = Path(input_dir)
            self.output_dir = Path(output_dir)
        
        # Crea le directory di output
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.delta_log_dir = self.output_dir / "delta_log"
        self.delta_log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Input directory: {self.input_dir.absolute()}")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info(f"Delta log directory: {self.delta_log_dir.absolute()}")
        
    def load_all_json_files(self) -> List[Dict[str, Any]]:
        """Carica tutti i file JSON dalla directory di input"""
        all_data = []
        json_files = list(self.input_dir.glob("*.json"))
        
        logger.info(f"Trovati {len(json_files)} file JSON da processare")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Aggiungi il nome del file sorgente a ogni record
                        for record in data:
                            record['source_file'] = json_file.name
                        all_data.extend(data)
                    else:
                        data['source_file'] = json_file.name
                        all_data.append(data)
                logger.info(f"Caricato {json_file.name}: {len(data) if isinstance(data, list) else 1} record")
            except Exception as e:
                logger.error(f"Errore nel caricamento di {json_file}: {e}")
                
        logger.info(f"Totale record caricati: {len(all_data)}")
        return all_data
    
    def deduplicate_by_url(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplica i dati per URL, mantenendo il record più recente"""
        seen_urls = {}
        
        for record in data:
            url = record.get('url')
            if not url:
                continue
                
            # Se l'URL esiste già, confronta i timestamp e mantieni il più recente
            if url in seen_urls:
                current_time = record.get('ingestion_timestamp', '')
                existing_time = seen_urls[url].get('ingestion_timestamp', '')
                
                if current_time > existing_time:
                    seen_urls[url] = record
            else:
                seen_urls[url] = record
        
        deduplicated_data = list(seen_urls.values())
        logger.info(f"Deduplicazione completata: {len(data)} -> {len(deduplicated_data)} record")
        return deduplicated_data
    
    def create_topics_table(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Crea la tabella topics esplodendo l'array topics"""
        topics_records = []
        
        for record in data:
            url = record.get('url')
            if not url:
                continue
                
            # Metadati della news
            news_metadata = {
                'url': url,
                'title': record.get('title', ''),
                'summary': record.get('summary', ''),
                'authors': json.dumps(record.get('authors', []), ensure_ascii=False),
                'time_published': record.get('time_published', ''),
                'source': record.get('source', ''),
                'source_domain': record.get('source_domain', ''),
                'category_within_source': record.get('category_within_source', ''),
                'banner_image': record.get('banner_image', ''),
                'overall_sentiment_score': record.get('overall_sentiment_score', 0),
                'overall_sentiment_label': record.get('overall_sentiment_label', ''),
                'source_ticker': record.get('source_ticker', ''),
                'ingestion_timestamp': record.get('ingestion_timestamp', ''),
                'source_file': record.get('source_file', '')
            }
            
            # Esplodi l'array topics
            topics = record.get('topics', [])
            if topics:
                for topic in topics:
                    topic_record = news_metadata.copy()
                    topic_record.update({
                        'topic': topic.get('topic', ''),
                        'relevance_score': topic.get('relevance_score', 0)
                    })
                    topics_records.append(topic_record)
            else:
                # Se non ci sono topics, crea un record con topic vuoto
                topic_record = news_metadata.copy()
                topic_record.update({
                    'topic': '',
                    'relevance_score': 0
                })
                topics_records.append(topic_record)
        
        df = pd.DataFrame(topics_records)
        logger.info(f"Tabella topics creata: {len(df)} record")
        return df
    
    def create_tickers_table(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Crea la tabella tickers esplodendo l'array ticker_sentiment"""
        tickers_records = []
        
        for record in data:
            url = record.get('url')
            if not url:
                continue
                
            # Metadati della news
            news_metadata = {
                'url': url,
                'title': record.get('title', ''),
                'summary': record.get('summary', ''),
                'authors': json.dumps(record.get('authors', []), ensure_ascii=False),
                'time_published': record.get('time_published', ''),
                'source': record.get('source', ''),
                'source_domain': record.get('source_domain', ''),
                'category_within_source': record.get('category_within_source', ''),
                'banner_image': record.get('banner_image', ''),
                'overall_sentiment_score': record.get('overall_sentiment_score', 0),
                'overall_sentiment_label': record.get('overall_sentiment_label', ''),
                'source_ticker': record.get('source_ticker', ''),
                'ingestion_timestamp': record.get('ingestion_timestamp', ''),
                'source_file': record.get('source_file', '')
            }
            
            # Esplodi l'array ticker_sentiment
            ticker_sentiments = record.get('ticker_sentiment', [])
            if ticker_sentiments:
                for ticker_sentiment in ticker_sentiments:
                    ticker_record = news_metadata.copy()
                    ticker_record.update({
                        'ticker': ticker_sentiment.get('ticker', ''),
                        'relevance_score': ticker_sentiment.get('relevance_score', 0),
                        'ticker_sentiment_score': ticker_sentiment.get('ticker_sentiment_score', 0),
                        'ticker_sentiment_label': ticker_sentiment.get('ticker_sentiment_label', '')
                    })
                    tickers_records.append(ticker_record)
            else:
                # Se non ci sono ticker_sentiment, crea un record con ticker vuoto
                ticker_record = news_metadata.copy()
                ticker_record.update({
                    'ticker': '',
                    'relevance_score': 0,
                    'ticker_sentiment_score': 0,
                    'ticker_sentiment_label': ''
                })
                tickers_records.append(ticker_record)
        
        df = pd.DataFrame(tickers_records)
        logger.info(f"Tabella tickers creata: {len(df)} record")
        return df
    
    def save_tables(self, topics_df: pd.DataFrame, tickers_df: pd.DataFrame):
        """Salva le tabelle in formato CSV con timestamp e delta logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Delta logging per topics
        topics_insertions, topics_deletions = self.calculate_delta(topics_df, "topics")
        self.save_delta_log("topics", topics_insertions, topics_deletions, timestamp)
        self.save_current_state(topics_df, "topics")
        
        # Delta logging per tickers
        tickers_insertions, tickers_deletions = self.calculate_delta(tickers_df, "tickers")
        self.save_delta_log("tickers", tickers_insertions, tickers_deletions, timestamp)
        self.save_current_state(tickers_df, "tickers")
        
        # Salva solo le versioni per overwrite (il delta log mantiene lo storico)
        topics_file = self.output_dir / "topics.csv"
        topics_df.to_csv(topics_file, index=False, encoding='utf-8')
        logger.info(f"Tabella topics salvata: {topics_file}")
        
        tickers_file = self.output_dir / "tickers.csv"
        tickers_df.to_csv(tickers_file, index=False, encoding='utf-8')
        logger.info(f"Tabella tickers salvata: {tickers_file}")
        
        return topics_file, tickers_file
    
    def process(self):
        """Processo completo di elaborazione"""
        logger.info("Inizio elaborazione dati news")
        
        # 1. Carica tutti i file JSON
        data = self.load_all_json_files()
        
        if not data:
            logger.warning("Nessun dato trovato da processare")
            return
        
        # 2. Deduplica per URL
        deduplicated_data = self.deduplicate_by_url(data)
        
        # 3. Crea tabella topics
        topics_df = self.create_topics_table(deduplicated_data)
        
        # 4. Crea tabella tickers
        tickers_df = self.create_tickers_table(deduplicated_data)
        
        # 5. Salva le tabelle
        topics_file, tickers_file = self.save_tables(topics_df, tickers_df)
        
        # 6. Statistiche finali
        logger.info("=== STATISTICHE FINALI ===")
        logger.info(f"Record originali: {len(data)}")
        logger.info(f"Record dopo deduplicazione: {len(deduplicated_data)}")
        logger.info(f"Record nella tabella topics: {len(topics_df)}")
        logger.info(f"Record nella tabella tickers: {len(tickers_df)}")
        logger.info(f"URL unici: {topics_df['url'].nunique()}")
        logger.info(f"Topics unici: {topics_df['topic'].nunique()}")
        logger.info(f"Tickers unici: {tickers_df['ticker'].nunique()}")
        
        logger.info("Elaborazione completata con successo!")
    
    def generate_record_hash(self, record: Dict[str, Any], table_name: str) -> str:
        """Genera un hash univoco per un record basato sui campi chiave specifici per tabella"""
        if table_name == "topics":
            # Per topics: URL + topic
            key_fields = [
                record.get('url', ''),
                record.get('topic', '')
            ]
        elif table_name == "tickers":
            # Per tickers: URL + ticker
            key_fields = [
                record.get('url', ''),
                record.get('ticker', '')
            ]
        else:
            raise ValueError(f"Tabella non supportata: {table_name}")
        
        key_string = '|'.join(str(field) for field in key_fields)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def load_previous_state(self, table_name: str) -> Set[str]:
        """Carica lo stato precedente di una tabella dal delta log"""
        previous_file = self.delta_log_dir / f"{table_name}_previous_hashes.txt"
        if previous_file.exists():
            with open(previous_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()
    
    def save_current_state(self, df: pd.DataFrame, table_name: str):
        """Salva lo stato corrente di una tabella nel delta log"""
        current_hashes = set()
        for _, row in df.iterrows():
            record = row.to_dict()
            hash_value = self.generate_record_hash(record, table_name)
            current_hashes.add(hash_value)
        
        # Salva gli hash correnti
        current_file = self.delta_log_dir / f"{table_name}_current_hashes.txt"
        with open(current_file, 'w') as f:
            for hash_value in sorted(current_hashes):
                f.write(f"{hash_value}\n")
        
        # Sposta il file corrente come precedente per la prossima esecuzione
        previous_file = self.delta_log_dir / f"{table_name}_previous_hashes.txt"
        if current_file.exists():
            current_file.rename(previous_file)
    
    def calculate_delta(self, df: pd.DataFrame, table_name: str) -> Tuple[List[Dict], List[Dict]]:
        """Calcola le inserzioni e cancellazioni rispetto allo stato precedente"""
        current_hashes = set()
        hash_to_record = {}
        
        # Genera hash per tutti i record correnti
        for _, row in df.iterrows():
            record = row.to_dict()
            hash_value = self.generate_record_hash(record, table_name)
            current_hashes.add(hash_value)
            hash_to_record[hash_value] = record
        
        # Carica hash precedenti
        previous_hashes = self.load_previous_state(table_name)
        
        # Calcola inserzioni (presenti ora, non prima)
        insertions = [hash_to_record[hash_value] for hash_value in current_hashes - previous_hashes]
        
        # Calcola cancellazioni (presenti prima, non ora)
        deletions = list(previous_hashes - current_hashes)
        
        return insertions, deletions
    
    def save_delta_log(self, table_name: str, insertions: List[Dict], deletions: List[str], timestamp: str):
        """Salva il log delle modifiche"""
        delta_file = self.delta_log_dir / f"{table_name}_delta_{timestamp}.json"
        
        delta_data = {
            'timestamp': timestamp,
            'table_name': table_name,
            'insertions_count': len(insertions),
            'deletions_count': len(deletions),
            'insertions': insertions,
            'deletions': deletions
        }
        
        with open(delta_file, 'w', encoding='utf-8') as f:
            json.dump(delta_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Delta log salvato per {table_name}: {len(insertions)} inserzioni, {len(deletions)} cancellazioni")

def main():
    """Funzione principale"""
    processor = NewsDataProcessor()
    processor.process()

if __name__ == "__main__":
    main()
