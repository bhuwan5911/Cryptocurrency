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
