from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    crypto = Column(String(10), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    predicted_price = Column(Float, nullable=False)
    actual_price = Column(Float, nullable=True)
    prediction_date = Column(String(20), nullable=False)  # Date for which prediction was made
    
    def __repr__(self):
        return f'<Prediction {self.crypto}: ${self.predicted_price} for {self.prediction_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'crypto': self.crypto,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'predicted_price': round(self.predicted_price, 2),
            'actual_price': round(self.actual_price, 2) if self.actual_price is not None else None,
            'prediction_date': self.prediction_date
        }

class PortfolioHolding(db.Model):
    __tablename__ = 'portfolio_holdings'
    
    id = Column(Integer, primary_key=True)
    crypto = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)  # Amount of crypto owned
    purchase_price = Column(Float, nullable=False)  # Price when bought
    purchase_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PortfolioHolding {self.crypto}: {self.amount} @ ${self.purchase_price}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'crypto': self.crypto,
            'amount': self.amount,
            'purchase_price': round(self.purchase_price, 2),
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d'),
            'notes': self.notes or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
