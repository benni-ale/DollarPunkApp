#!/usr/bin/env python3
"""
Script per riorganizzare i file JSON delle news:
1. Crea la directory ingested
2. Sposta tutti i file news_data_* nella directory ingested
3. Rinomina i file cambiando il formato: news_data_batch_0001_20250808_100548 -> news_data_batch_20250808_100548_0001
"""

import os
import re
import shutil
from pathlib import Path
import logging
from datetime import datetime

# Configurazione logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reorganize_news_files(output_dir: str = "../output"):
    """Riorganizza i file JSON delle news"""
    
    output_path = Path(output_dir)
    if not output_path.exists():
        logger.error(f"Directory {output_dir} non trovata")
        return
    
    # Crea la directory ingested
    ingested_dir = output_path / "ingested"
    ingested_dir.mkdir(exist_ok=True)
    logger.info(f"Directory creata: {ingested_dir}")
    
    # Trova tutti i file news_data_*.json
    news_files = list(output_path.glob("news_data_*.json"))
    logger.info(f"Trovati {len(news_files)} file news_data da riorganizzare")
    
    moved_count = 0
    renamed_count = 0
    
    for file_path in news_files:
        try:
            # Pattern per estrarre le parti del nome
            # news_data_batch_0001_20250808_100548.json
            pattern = r'news_data_batch_(\d+)_(\d{8})_(\d{6})\.json'
            match = re.match(pattern, file_path.name)
            
            if match:
                batch_num = match.group(1)
                date_part = match.group(2)
                time_part = match.group(3)
                
                # Nuovo formato: news_data_batch_20250808_100548_0001.json
                new_name = f"news_data_batch_{date_part}_{time_part}_{batch_num}.json"
                new_path = ingested_dir / new_name
                
                # Sposta e rinomina il file
                shutil.move(str(file_path), str(new_path))
                logger.info(f"Spostato e rinominato: {file_path.name} -> {new_name}")
                moved_count += 1
                renamed_count += 1
                
            else:
                # Se non matcha il pattern, sposta solo senza rinominare
                new_path = ingested_dir / file_path.name
                shutil.move(str(file_path), str(new_path))
                logger.info(f"Spostato: {file_path.name}")
                moved_count += 1
                
        except Exception as e:
            logger.error(f"Errore nel processare {file_path.name}: {e}")
    
    logger.info(f"Riorganizzazione completata:")
    logger.info(f"- File spostati: {moved_count}")
    logger.info(f"- File rinominati: {renamed_count}")
    logger.info(f"- Directory di destinazione: {ingested_dir}")

def main():
    """Funzione principale"""
    logger.info("Inizio riorganizzazione file news")
    reorganize_news_files()
    logger.info("Riorganizzazione completata!")

if __name__ == "__main__":
    main()
