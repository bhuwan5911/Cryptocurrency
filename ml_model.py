import numpy as np
import pandas as pd
import yfinance as yf
import pickle
import os
import logging
from datetime import datetime, timedelta

# NAYE IMPORTS (Phase 2 ke liye)
from sklearn.preprocessing import MinMaxScaler # Data ko 0-1 scale karne ke liye
from tensorflow.keras.models import Sequential, load_model # Naya model banane aur load karne ke liye
from tensorflow.keras.layers import LSTM, Dense, Dropout # Model ki layers

class CryptoPredictionModel:
    def __init__(self):
        self.models = {} # Trained models (dimag) yahaan store honge
        self.scalers = {} # Scalers (0-1 converter) yahaan store honge
        self.lookback_days = 60 # IMPORTANT: Hum 5 din ki jagah ab 60 din ka data dekhenge
        
        # models/ folder banao agar nahi hai toh
        if not os.path.exists('models'):
            os.makedirs('models')
        
        # Scalers ko save karne ke liye folder
        if not os.path.exists('scalers'):
            os.makedirs('scalers')

        # App start hote hi, saare models ko load ya train karo
        self.load_or_train_models()
    
    def get_crypto_data(self, symbol, period="2y"):
        """Yahoo Finance se data fetch karna (Yeh function same hai)"""
        try:
            ticker = f"{symbol}-USD"
            # auto_adjust=True fixes some pandas warnings
            data = yf.download(ticker, period=period, interval="1d", auto_adjust=True)
            if data is None or data.empty:
                logging.error(f"No data found for {ticker}")
                return None
            return data
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _build_lstm_model(self):
        """
        YEH NAYA FUNCTION HAI
        Yeh hamara naya "Shahi Biryani" (Stacked LSTM) model ka architecture banata hai.
        """
        model = Sequential()
        
        # Layer 1: Pehli LSTM layer (50 units)
        # return_sequences=True ka matlab hai ki data ko agli layer par bhejo
        model.add(LSTM(units=50, return_sequences=True, input_shape=(self.lookback_days, 1)))
        model.add(Dropout(0.2)) # 20% neurons ko 'band' kardo (overfitting rokne ke liye)
        
        # Layer 2: Doosri LSTM layer
        model.add(LSTM(units=50, return_sequences=True))
        model.add(Dropout(0.2))
        
        # Layer 3: Teesri LSTM layer
        # return_sequences=False ka matlab hai ki ab bas final output do
        model.add(LSTM(units=50, return_sequences=False))
        model.add(Dropout(0.2))
        
        # Layer 4: Final Output Layer
        # Dense(1) ka matlab hai ki humein 1 number (agle din ka price) predict karna hai
        model.add(Dense(units=1))
        
        # Model ko compile karo
        model.compile(optimizer='adam', loss='mean_squared_error')
        return model

    def prepare_features(self, scaled_data):
        """
        YEH FUNCTION UPDATE HO GAYA HAI
        Ab yeh data ko 3D "chunks" (tukdon) mein todta hai.
        """
        X, y = [], []
        
        # 60 din ka data (X) lo, aur 61st din ka data (y) predict karo
        for i in range(self.lookback_days, len(scaled_data)):
            X.append(scaled_data[i-self.lookback_days:i, 0])
            y.append(scaled_data[i, 0])
            
        return np.array(X), np.array(y)
    
    def train_model(self, symbol):
        """
        YEH FUNCTION POORI TARAH BADAL GAYA HAI
        Ab yeh Linear Regression nahi, LSTM model train karta hai.
        """
        logging.info(f"Starting NEW LSTM model training for {symbol}...")
        
        # 1. Data Fetch Karo
        data = self.get_crypto_data(symbol, period="3y") # 3 saal ka data lete hain
        if data is None:
            logging.error(f"Could not get data for {symbol}")
            return False
        
        # Sirf 'Close' price ka data lo
        close_prices = data['Close'].values.reshape(-1, 1)

        # 2. Data Ko Scale Karo (0 se 1 ke beech)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(close_prices)
        
        # 3. Data Ko Reshape Karo (LSTM ke liye)
        X, y = self.prepare_features(scaled_data)
        if X is None or len(X) == 0:
            logging.error(f"Could not prepare features for {symbol}")
            return False
            
        # Reshape X to 3D: [samples, timesteps, features]
        # (Number of samples, 60 days, 1 feature (price))
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))
        
        # 4. Model Build Karo
        model = self._build_lstm_model()
        
        # 5. Model Train Karo
        # epochs=25 ka matlab hai ki model data ko 25 baar dekhega
        logging.info(f"Training LSTM for {symbol}... This will take time.")
        model.fit(X, y, epochs=25, batch_size=32, verbose=1)
        
        # 6. Naya Model Aur Scaler Save Karo
        model_path = f"models/model_{symbol.lower()}.keras" # .pkl nahi, .keras
        scaler_path = f"scalers/scaler_{symbol.lower()}.pkl"
        
        model.save(model_path) # Keras model ko aise save karte hain
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f) # Scaler ko waise hi pickle karte hain
            
        # Inhe memory mein bhi store karo
        self.models[symbol] = model
        self.scalers[symbol] = scaler
        
        logging.info(f"NEW LSTM Model for {symbol} saved to {model_path}")
        return True
    
    def load_or_train_models(self):
        """
        YEH FUNCTION UPDATE HO GAYA HAI
        Ab yeh .keras (model) aur .pkl (scaler) files ko dhoondta hai
        """
        # HACKATHON FIX: MATIC aur UNI ko list se hata diya
        symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        
        for symbol in symbols:
            model_path = f"models/model_{symbol.lower()}.keras"
            scaler_path = f"scalers/scaler_{symbol.lower()}.pkl"
            
            # Try to load existing model
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    self.models[symbol] = load_model(model_path) # Keras model aise load hota hai
                    with open(scaler_path, 'rb') as f:
                        self.scalers[symbol] = pickle.load(f)
                    logging.info(f"Loaded existing LSTM model and scaler for {symbol}")
                    continue
                except Exception as e:
                    logging.error(f"Error loading model for {symbol}: {e}. Retraining...")
            
            # Train new model if loading failed or model doesn't exist
            success = self.train_model(symbol)
            if not success:
                logging.error(f"Failed to train new LSTM model for {symbol}")
    
    def predict_price(self, symbol):
        """
        YEH FUNCTION FIX KIYA GAYA HAI (CRASH FIX)
        """
        if symbol not in self.models or symbol not in self.scalers:
            logging.error(f"No model or scaler available for {symbol}")
            return None
            
        try:
            # 1. Model aur Scaler ko memory se load karo
            model = self.models[symbol]
            scaler = self.scalers[symbol]
            
            # 2. Naya (Live) Data Fetch Karo (60 din + extra)
            data = self.get_crypto_data(symbol, period="90d") # 90 din ka data lete hain safe rehne ke liye
            if data is None or len(data) < self.lookback_days:
                logging.error(f"Not enough recent data for {symbol}")
                return None
            
            # 3. Data Ko Prepare Karo (Scaling + Reshaping)
            # Sirf pichle 60 din ka 'Close' price lo
            recent_prices = data['Close'].tail(self.lookback_days).values.reshape(-1, 1)
            
            # Is naye data ko *purane* (saved) scaler se 0-1 mein badlo
            scaled_input = scaler.transform(recent_prices)
            
            # Isse 3D shape mein badlo (LSTM ke liye)
            # (1 sample, 60 days, 1 feature)
            X_test = np.reshape(scaled_input, (1, self.lookback_days, 1))
            
            # 4. Prediction Karo
            scaled_prediction = model.predict(X_test)
            
            # 5. Prediction Ko "Un-scale" Karo (Sabse Zaroori)
            # Model 0.85 jaisa output dega, humein usse waapas $67,500 mein badalna hai
            predicted_price = scaler.inverse_transform(scaled_prediction)[0][0]
            
            # 6. Current Price Lo (Response ke liye)
            # --- FIX SHURU ---
            # Pehle, last price ko nikaalo
            current_price_series_or_scalar = data['Close'].iloc[-1]
            
            # Check karo ki kya woh Series hai (jaisa warning mein tha)
            if isinstance(current_price_series_or_scalar, pd.Series):
                 current_price = float(current_price_series_or_scalar.iloc[0])
            else:
                 current_price = float(current_price_series_or_scalar)
            # Ab 'current_price' 100% ek float (number) hai
            # --- FIX KHATAM ---

            logging.info(f"{symbol} - Current: ${current_price:.2f}, Predicted (LSTM): ${predicted_price:.2f}")
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'predicted_price': float(predicted_price),
                'change_percent': float((predicted_price - current_price) / current_price * 100),
                'prediction_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            }
        
        except Exception as e:
            # Error ko print karo taaki hum dekh sakein agar koi aur problem hai
            logging.error(f"Error predicting price for {symbol}: {e}", exc_info=True)
            return None

    def get_historical_data(self, symbol, days=30):
        """(Yeh function bhi warning ke liye fix kiya gaya hai)"""
        try:
            data = self.get_crypto_data(symbol, period=f"{days}d")
            if data is None:
                return None
            
            chart_data = []
            for date, row in data.iterrows():
                # --- FIX SHURU ---
                price_series_or_scalar = row['Close']
                if isinstance(price_series_or_scalar, pd.Series):
                    price_float = float(price_series_or_scalar.iloc[0])
                else:
                    price_float = float(price_series_or_scalar)
                # --- FIX KHATAM ---
                
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': price_float
                })
            
            return chart_data
        
        except Exception as e:
            logging.error(f"Error getting historical data for {symbol}: {e}")
            return None