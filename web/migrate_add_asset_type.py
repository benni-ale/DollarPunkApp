#!/usr/bin/env python3
"""
Script di migrazione per aggiungere la colonna asset_type alla tabella portfolio_positions
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def migrate_database():
    """Aggiunge la colonna asset_type se non esiste"""
    
    # Configurazione database
    database_url = os.getenv('DATABASE_URL', 'postgresql://dollarpunk_user:dollarpunk_password@postgres:5432/dollarpunk')
    
    try:
        # Crea la connessione al database
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Controlla se la colonna asset_type esiste già
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'portfolio_positions' 
                AND column_name = 'asset_type'
            """))
            
            if result.fetchone() is None:
                print("🔄 Aggiungo la colonna asset_type...")
                
                # Aggiungi la colonna asset_type con valore di default 'stock'
                conn.execute(text("""
                    ALTER TABLE portfolio_positions 
                    ADD COLUMN asset_type VARCHAR(20) DEFAULT 'stock' NOT NULL
                """))
                
                # Aggiorna tutte le righe esistenti per assicurarsi che abbiano il valore corretto
                conn.execute(text("""
                    UPDATE portfolio_positions 
                    SET asset_type = 'stock' 
                    WHERE asset_type IS NULL
                """))
                
                conn.commit()
                print("✅ Colonna asset_type aggiunta con successo!")
            else:
                print("ℹ️  La colonna asset_type esiste già")
                
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Avvio migrazione database...")
    success = migrate_database()
    
    if success:
        print("✅ Migrazione completata con successo!")
        sys.exit(0)
    else:
        print("❌ Migrazione fallita!")
        sys.exit(1)
