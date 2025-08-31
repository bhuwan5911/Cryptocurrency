import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pickle
import os
import logging
from datetime import datetime, timedelta

class CryptoPredictionModel:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.load_or_train_models()
    
    def get_crypto_data(self, symbol, period="1y"):
        """Fetch cryptocurrency data from Yahoo Finance"""
        try:
            ticker = f"{symbol}-USD"
            data = yf.download(ticker, period=period, interval="1d")
            if data is None or data.empty:
                logging.error(f"No data found for {ticker}")
                return None
            return data
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def prepare_features(self, data, lookback_days=5):
        """Prepare features using past N days to predict next day"""
        if data is None or len(data) < lookback_days + 1:
            return None, None
        
        # Use closing prices
        prices = data['Close'].values
        
        X, y = [], []
        for i in range(lookback_days, len(prices)):
            # Use past lookback_days prices as features - flatten to 1D
            X.append(prices[i-lookback_days:i].flatten())
            y.append(prices[i])
        
        return np.array(X), np.array(y)
    
    def train_model(self, symbol):
        """Train a Linear Regression model for a specific cryptocurrency"""
        logging.info(f"Training model for {symbol}")
        
        # Get historical data
        data = self.get_crypto_data(symbol, period="2y")
        if data is None:
            logging.error(f"Could not get data for {symbol}")
            return False
        
        # Prepare features
        X, y = self.prepare_features(data)
        if X is None or len(X) == 0:
            logging.error(f"Could not prepare features for {symbol}")
            return False
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        logging.info(f"{symbol} Model - MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        # Store model
        self.models[symbol] = model
        
        # Save model to file
        model_path = f"model_{symbol.lower()}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        logging.info(f"Model for {symbol} saved to {model_path}")
        return True
    
    def load_or_train_models(self):
        """Load existing models or train new ones"""
        symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'AVAX', 'LINK', 'UNI', 'LTC']
        
        for symbol in symbols:
            model_path = f"model_{symbol.lower()}.pkl"
            
            # Try to load existing model
            if os.path.exists(model_path):
                try:
                    with open(model_path, 'rb') as f:
                        self.models[symbol] = pickle.load(f)
                    logging.info(f"Loaded existing model for {symbol}")
                    continue
                except Exception as e:
                    logging.error(f"Error loading model for {symbol}: {e}")
            
            # Train new model if loading failed or model doesn't exist
            success = self.train_model(symbol)
            if not success:
                logging.error(f"Failed to train model for {symbol}")
    
    def predict_price(self, symbol, days_ahead=1):
        """Predict future price for a cryptocurrency"""
        if symbol not in self.models:
            logging.error(f"No model available for {symbol}")
            return None
        
        try:
            # Get recent data
            data = self.get_crypto_data(symbol, period="30d")
            if data is None:
                logging.error(f"Could not get recent data for {symbol}")
                return None
            
            # Get last 5 days of closing prices
            recent_prices = data['Close'].tail(5).values
            
            if len(recent_prices) < 5:
                logging.error(f"Not enough recent data for {symbol}")
                return None
            
            # Make prediction - reshape to match training data format
            model = self.models[symbol]
            prediction = model.predict([recent_prices.flatten()])[0]
            
            # Get current price for comparison
            current_price = data['Close'].iloc[-1]
            
            logging.info(f"{symbol} - Current: ${float(current_price.iloc[0] if hasattr(current_price, 'iloc') else current_price):.2f}, Predicted: ${float(prediction):.2f}")
            
            return {
                'symbol': symbol,
                'current_price': float(current_price.iloc[0] if hasattr(current_price, 'iloc') else current_price),
                'predicted_price': float(prediction),
                'change_percent': float((prediction - (current_price.iloc[0] if hasattr(current_price, 'iloc') else current_price)) / (current_price.iloc[0] if hasattr(current_price, 'iloc') else current_price) * 100),
                'prediction_date': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            }
        
        except Exception as e:
            logging.error(f"Error predicting price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol, days=30):
        """Get historical price data for charts"""
        try:
            data = self.get_crypto_data(symbol, period=f"{days}d")
            if data is None:
                return None
            
            # Format data for Chart.js
            chart_data = []
            for date, row in data.iterrows():
                chart_data.append({
                    'date': date.date().strftime('%Y-%m-%d') if hasattr(date, 'date') else str(date)[:10],
                    'price': float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
                })
            
            return chart_data
        
        except Exception as e:
            logging.error(f"Error getting historical data for {symbol}: {e}")
            return None
