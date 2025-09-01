from models import db, User, PortfolioPosition
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import time
import psycopg2

def wait_for_postgres(max_retries=30, delay=2):
    """Aspetta che PostgreSQL sia pronto per le connessioni"""
    print("⏳ Aspetto che PostgreSQL sia pronto...")
    
    for attempt in range(max_retries):
        try:
            # Prova a connettersi a PostgreSQL
            conn = psycopg2.connect(
                host="postgres",
                port="5432",
                database="dollarpunk",
                user="dollarpunk_user",
                password="dollarpunk_password"
            )
            conn.close()
            print(f"✅ PostgreSQL pronto dopo {attempt + 1} tentativi")
            return True
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"⏳ Tentativo {attempt + 1}/{max_retries}: PostgreSQL non ancora pronto, riprovo tra {delay} secondi...")
                time.sleep(delay)
            else:
                print(f"❌ PostgreSQL non disponibile dopo {max_retries} tentativi")
                return False
    return False

def init_db(app):
    """Inizializza il database"""
    db.init_app(app)
    
    # Aspetta che PostgreSQL sia pronto
    if not wait_for_postgres():
        print("❌ Impossibile connettersi a PostgreSQL")
        return False
    
    with app.app_context():
        try:
            # Crea tutte le tabelle
            db.create_all()
            print("✅ Tabelle database create")
            
            # Crea l'utente demo se non esiste
            create_demo_user()
            return True
        except Exception as e:
            print(f"❌ Errore nell'inizializzazione database: {e}")
            return False

def create_demo_user():
    """Crea l'utente demo se non esiste"""
    demo_user = User.query.filter_by(email='demo@dollarpunk.com').first()
    
    if not demo_user:
        demo_user = User(
            email='demo@dollarpunk.com',
            password_hash=generate_password_hash('demo123'),
            name='Demo User'
        )
        db.session.add(demo_user)
        db.session.commit()
        print("✅ Utente demo creato")

def get_user_by_email(email):
    """Ottiene un utente per email"""
    return User.query.filter_by(email=email).first()

def verify_user_password(user, password):
    """Verifica la password di un utente"""
    return check_password_hash(user.password_hash, password)

def get_user_portfolio(user_id):
    """Ottiene tutte le posizioni del portafoglio di un utente"""
    positions = PortfolioPosition.query.filter_by(user_id=user_id).all()
    return [pos.to_dict() for pos in positions]

def add_portfolio_position(user_id, symbol, quantity, purchase_date, avg_price, asset_type='stock'):
    """Aggiunge una posizione al portafoglio"""
    try:
        # Ora permettiamo più posizioni dello stesso simbolo
        position = PortfolioPosition(
            user_id=user_id,
            symbol=symbol,
            quantity=quantity,
            purchase_date=purchase_date,
            avg_price=avg_price,
            asset_type=asset_type
        )
        db.session.add(position)
        db.session.commit()
        return True, "Posizione salvata con successo"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Errore nel salvataggio: {str(e)}"

def remove_portfolio_position(user_id, position_id):
    """Rimuove una posizione dal portafoglio per ID"""
    try:
        position = PortfolioPosition.query.filter_by(
            user_id=user_id,
            id=position_id
        ).first()

        if position:
            symbol = position.symbol
            db.session.delete(position)
            db.session.commit()
            return True, f"Posizione {symbol} rimossa con successo"
        else:
            return False, f"Posizione con ID {position_id} non trovata"

    except Exception as e:
        db.session.rollback()
        return False, f"Errore nella rimozione: {str(e)}"

def update_portfolio_position(user_id, position_id, quantity, purchase_date, avg_price):
    """Aggiorna una posizione esistente per ID"""
    try:
        position = PortfolioPosition.query.filter_by(
            user_id=user_id,
            id=position_id
        ).first()

        if position:
            position.quantity = quantity
            position.purchase_date = purchase_date
            position.avg_price = avg_price
            position.updated_at = datetime.utcnow()
            db.session.commit()
            return True, "Posizione aggiornata con successo"
        else:
            return False, f"Posizione con ID {position_id} non trovata"

    except Exception as e:
        db.session.rollback()
        return False, f"Errore nell'aggiornamento: {str(e)}"
