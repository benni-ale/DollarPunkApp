from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """Modello per gli utenti"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relazione con le posizioni del portafoglio
    portfolio_positions = db.relationship('PortfolioPosition', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class PortfolioPosition(db.Model):
    """Modello per le posizioni del portafoglio"""
    __tablename__ = 'portfolio_positions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    user = db.relationship('User', backref=db.backref('positions', lazy=True))
    
    def __repr__(self):
        return f'<PortfolioPosition {self.symbol} x {self.quantity}>'
    
    def to_dict(self):
        """Converte la posizione in dizionario"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'quantity': float(self.quantity),
            'purchase_date': self.purchase_date.isoformat(),
            'avg_price': float(self.avg_price),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


