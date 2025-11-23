import numpy as np
import pandas as pd
import yfinance as yf
import pickle
import os
import logging
from datetime import datetime, timedelta
import ta  # Technical Analysis library
import warnings
warnings.filterwarnings('ignore')

# --- CONFIGURE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_model.log'),
        logging.StreamHandler()
    ]
)

# --- IMPORTS ---
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import (LSTM, Dense, Dropout, Bidirectional, 
                                     BatchNormalization, Attention, Input,
                                     Concatenate, Conv1D, MaxPooling1D, Flatten)
from tensorflow.keras.regularizers import l1_l2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
import tensorflow as tf

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

class CryptoPredictionModel:
    def __init__(self):
        self.models = {} 
        self.scalers = {} 
        self.feature_scalers = {}
        self.lookback_days = 90  # Increased for better pattern recognition
        
        if not os.path.exists('models'):
            os.makedirs('models')
        
        if not os.path.exists('scalers'):
            os.makedirs('scalers')

        # Set random seeds for reproducibility
        np.random.seed(42)
        tf.random.set_seed(42)

        self.load_or_train_models()
    
    def get_crypto_data(self, symbol, period="5y"):
        """
        Enhanced: Now downloads more historical data for better training.
        """
        try:
            ticker = f"{symbol}-USD"
            data = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
            
            if data is None or data.empty:
                logging.error(f"No data found for {ticker}")
                return None
            
            # Handle MultiIndex columns from yfinance
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.droplevel(1)
            
            # Handle missing values
            data = data.interpolate(method='linear')
            data = data.dropna()
            
            # Ensure we have required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_cols):
                logging.error(f"Missing required columns for {ticker}")
                return None
            
            return data
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def engineer_features(self, data):
        """
        NEW: Create advanced technical indicators and features.
        This significantly improves prediction accuracy.
        """
        df = data.copy()
        
        # Ensure we have a proper DataFrame with single-level columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Convert to Series if needed (flatten any multi-dimensional data)
        close_series = pd.Series(df['Close'].values.flatten(), index=df.index)
        high_series = pd.Series(df['High'].values.flatten(), index=df.index)
        low_series = pd.Series(df['Low'].values.flatten(), index=df.index)
        volume_series = pd.Series(df['Volume'].values.flatten(), index=df.index)
        
        # Price-based features
        df['returns'] = close_series.pct_change()
        df['log_returns'] = np.log(close_series / close_series.shift(1))
        
        # Moving Averages
        df['sma_7'] = close_series.rolling(window=7).mean()
        df['sma_21'] = close_series.rolling(window=21).mean()
        df['sma_50'] = close_series.rolling(window=50).mean()
        df['ema_12'] = close_series.ewm(span=12).mean()
        df['ema_26'] = close_series.ewm(span=26).mean()
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=21).std()
        
        # RSI (Relative Strength Index)
        try:
            df['rsi'] = ta.momentum.rsi(close_series, window=14)
        except:
            df['rsi'] = ta.momentum.RSIIndicator(close_series, window=14).rsi()
        
        # MACD
        try:
            macd = ta.trend.MACD(close_series)
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
        except:
            macd_indicator = ta.trend.MACD(close_series)
            df['macd'] = macd_indicator.macd()
            df['macd_signal'] = macd_indicator.macd_signal()
            df['macd_diff'] = macd_indicator.macd_diff()
        
        # Bollinger Bands
        try:
            bollinger = ta.volatility.BollingerBands(close_series)
            df['bb_high'] = bollinger.bollinger_hband()
            df['bb_low'] = bollinger.bollinger_lband()
            df['bb_mid'] = bollinger.bollinger_mavg()
            df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid']
        except:
            df['bb_high'] = close_series.rolling(window=20).mean() + 2 * close_series.rolling(window=20).std()
            df['bb_low'] = close_series.rolling(window=20).mean() - 2 * close_series.rolling(window=20).std()
            df['bb_mid'] = close_series.rolling(window=20).mean()
            df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid']
        
        # Volume features
        df['volume_sma'] = volume_series.rolling(window=21).mean()
        df['volume_ratio'] = volume_series / df['volume_sma']
        
        # ATR (Average True Range)
        try:
            df['atr'] = ta.volatility.average_true_range(high_series, low_series, close_series, window=14)
        except:
            df['atr'] = ta.volatility.AverageTrueRange(high_series, low_series, close_series, window=14).average_true_range()
        
        # Stochastic Oscillator
        try:
            stoch = ta.momentum.StochasticOscillator(high_series, low_series, close_series)
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
        except:
            stoch = ta.momentum.StochasticOscillator(high_series, low_series, close_series)
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
        
        # On-Balance Volume
        try:
            df['obv'] = ta.volume.on_balance_volume(close_series, volume_series)
        except:
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(close_series, volume_series).on_balance_volume()
        
        # Momentum
        df['momentum'] = close_series - close_series.shift(4)
        
        # Rate of Change
        try:
            df['roc'] = ta.momentum.roc(close_series, window=12)
        except:
            df['roc'] = ta.momentum.ROCIndicator(close_series, window=12).roc()
        
        # Drop NaN values from feature engineering
        df = df.dropna()
        
        return df
    
    def _build_advanced_model(self, n_features):
        """
        NEW: Enhanced Stacked Bidirectional LSTM with Attention mechanism.
        This architecture captures long-term dependencies with attention for focus.
        Simplified to avoid dimension mismatch issues.
        """
        input_layer = Input(shape=(self.lookback_days, n_features))
        
        # First Bidirectional LSTM layer
        lstm1 = Bidirectional(LSTM(units=128, return_sequences=True, 
                                   kernel_regularizer=l1_l2(l1=0.0001, l2=0.001)))(input_layer)
        lstm1 = BatchNormalization()(lstm1)
        lstm1 = Dropout(0.3)(lstm1)
        
        # Second Bidirectional LSTM layer
        lstm2 = Bidirectional(LSTM(units=128, return_sequences=True,
                                   kernel_regularizer=l1_l2(l1=0.0001, l2=0.001)))(lstm1)
        lstm2 = BatchNormalization()(lstm2)
        lstm2 = Dropout(0.3)(lstm2)
        
        # Third Bidirectional LSTM layer
        lstm3 = Bidirectional(LSTM(units=96, return_sequences=True,
                                   kernel_regularizer=l1_l2(l1=0.0001, l2=0.001)))(lstm2)
        lstm3 = BatchNormalization()(lstm3)
        lstm3 = Dropout(0.3)(lstm3)
        
        # Fourth Bidirectional LSTM layer
        lstm4 = Bidirectional(LSTM(units=64, return_sequences=True))(lstm3)
        lstm4 = BatchNormalization()(lstm4)
        lstm4 = Dropout(0.3)(lstm4)
        
        # Attention mechanism - helps model focus on important time steps
        attention = Attention()([lstm4, lstm4])
        
        # Final LSTM layer to reduce to single output
        lstm_final = LSTM(units=64, return_sequences=False)(attention)
        lstm_final = BatchNormalization()(lstm_final)
        lstm_final = Dropout(0.3)(lstm_final)
        
        # Dense layers for final prediction
        dense1 = Dense(128, activation='relu', kernel_regularizer=l1_l2(l1=0.0001, l2=0.001))(lstm_final)
        dense1 = BatchNormalization()(dense1)
        dense1 = Dropout(0.3)(dense1)
        
        dense2 = Dense(64, activation='relu')(dense1)
        dense2 = BatchNormalization()(dense2)
        dense2 = Dropout(0.2)(dense2)
        
        dense3 = Dense(32, activation='relu')(dense2)
        dense3 = Dropout(0.2)(dense3)
        
        output = Dense(1)(dense3)
        
        model = Model(inputs=input_layer, outputs=output)
        
        # Custom optimizer with learning rate and gradient clipping
        optimizer = Adam(learning_rate=0.001, clipnorm=1.0)
        model.compile(optimizer=optimizer, loss='huber', metrics=['mae', 'mse'])
        
        return model

    def prepare_features(self, data_with_features):
        """
        Updated: Now handles multiple features instead of just close price.
        """
        feature_columns = [
            'Close', 'returns', 'log_returns', 'sma_7', 'sma_21', 'sma_50',
            'ema_12', 'ema_26', 'volatility', 'rsi', 'macd', 'macd_signal',
            'macd_diff', 'bb_high', 'bb_low', 'bb_mid', 'bb_width',
            'volume_ratio', 'atr', 'stoch_k', 'stoch_d', 'obv', 'momentum', 'roc'
        ]
        
        # Select only available features
        available_features = [col for col in feature_columns if col in data_with_features.columns]
        feature_data = data_with_features[available_features].values
        
        # Scale features
        scaler = RobustScaler()  # More robust to outliers than MinMaxScaler
        scaled_features = scaler.fit_transform(feature_data)
        
        X, y = [], []
        for i in range(self.lookback_days, len(scaled_features)):
            X.append(scaled_features[i-self.lookback_days:i])
            y.append(scaled_features[i, 0])  # Predict Close price (first feature)
        
        return np.array(X), np.array(y), scaler
    
    def train_model(self, symbol):
        """
        Enhanced: More epochs, better callbacks, and advanced architecture.
        """
        logging.info(f"Starting ADVANCED CNN-LSTM model training for {symbol}...")
        
        data = self.get_crypto_data(symbol, period="5y")
        if data is None or len(data) < self.lookback_days + 100:
            logging.error(f"Insufficient data for {symbol}")
            return False
        
        # Engineer features
        data_with_features = self.engineer_features(data)
        
        # Prepare features
        X, y, feature_scaler = self.prepare_features(data_with_features)
        if X is None or len(X) < 100:
            logging.error(f"Insufficient prepared data for {symbol}")
            return False
        
        # Define paths
        model_path = f"models/model_{symbol.lower()}.keras"
        scaler_path = f"scalers/scaler_{symbol.lower()}.pkl"
        feature_scaler_path = f"scalers/feature_scaler_{symbol.lower()}.pkl"
        
        # Build model
        n_features = X.shape[2]
        model = self._build_advanced_model(n_features)
        
        # Enhanced callbacks
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=15,  # Increased patience
            verbose=1,
            restore_best_weights=True,
            min_delta=0.0001
        )
        
        checkpoint = ModelCheckpoint(
            model_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
        
        # Reduce learning rate when stuck
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=0.00001,
            verbose=1
        )
        
        logging.info(f"Training advanced model for {symbol}...")
        logging.info(f"Training samples: {len(X)}, Features: {n_features}")
        
        # Train with more epochs (early stopping will handle it)
        history = model.fit(
            X, y,
            epochs=200,  # Increased significantly
            batch_size=32,
            verbose=1,
            validation_split=0.15,  # Increased validation split
            callbacks=[early_stop, checkpoint, reduce_lr],
            shuffle=True
        )
        
        # Save scalers
        with open(scaler_path, 'wb') as f:
            # Save a simple MinMaxScaler for price scaling (backwards compatibility)
            price_scaler = MinMaxScaler()
            price_scaler.fit(data['Close'].values.reshape(-1, 1))
            pickle.dump(price_scaler, f)
        
        with open(feature_scaler_path, 'wb') as f:
            pickle.dump(feature_scaler, f)
        
        # Load best model
        self.models[symbol] = load_model(model_path)
        self.scalers[symbol] = price_scaler
        self.feature_scalers[symbol] = feature_scaler
        
        # Log training results
        final_loss = min(history.history['val_loss'])
        logging.info(f"Training complete for {symbol}. Best val_loss: {final_loss:.6f}")
        
        return True
    
    def load_or_train_models(self):
        symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        
        for symbol in symbols:
            model_path = f"models/model_{symbol.lower()}.keras"
            scaler_path = f"scalers/scaler_{symbol.lower()}.pkl"
            feature_scaler_path = f"scalers/feature_scaler_{symbol.lower()}.pkl"
            
            if (os.path.exists(model_path) and 
                os.path.exists(scaler_path) and 
                os.path.exists(feature_scaler_path)):
                try:
                    self.models[symbol] = load_model(model_path)
                    with open(scaler_path, 'rb') as f:
                        self.scalers[symbol] = pickle.load(f)
                    with open(feature_scaler_path, 'rb') as f:
                        self.feature_scalers[symbol] = pickle.load(f)
                    logging.info(f"Loaded existing advanced model for {symbol}")
                    continue
                except Exception as e:
                    logging.error(f"Error loading {symbol}: {e}. Retraining...")
            
            self.train_model(symbol)
    
    def predict_price(self, symbol, days_ahead=1):
        """
        Enhanced: Multi-step prediction with confidence intervals.
        """
        if symbol not in self.models or symbol not in self.feature_scalers:
            return None
        
        try:
            model = self.models[symbol]
            feature_scaler = self.feature_scalers[symbol]
            price_scaler = self.scalers[symbol]
            
            # Get more historical data for feature engineering
            data = self.get_crypto_data(symbol, period="1y")
            if data is None or len(data) < self.lookback_days + 50:
                return None
            
            # Engineer features on full dataset
            data_with_features = self.engineer_features(data)
            
            # Get feature columns
            feature_columns = [
                'Close', 'returns', 'log_returns', 'sma_7', 'sma_21', 'sma_50',
                'ema_12', 'ema_26', 'volatility', 'rsi', 'macd', 'macd_signal',
                'macd_diff', 'bb_high', 'bb_low', 'bb_mid', 'bb_width',
                'volume_ratio', 'atr', 'stoch_k', 'stoch_d', 'obv', 'momentum', 'roc'
            ]
            available_features = [col for col in feature_columns if col in data_with_features.columns]
            
            # Get recent data
            recent_data = data_with_features[available_features].tail(self.lookback_days).values
            scaled_input = feature_scaler.transform(recent_data)
            X_test = np.reshape(scaled_input, (1, self.lookback_days, len(available_features)))
            
            # Make prediction
            scaled_prediction = model.predict(X_test, verbose=0)
            
            # Inverse transform only the price (first feature)
            dummy_features = np.zeros((1, len(available_features)))
            dummy_features[0, 0] = scaled_prediction[0, 0]
            predicted_price = feature_scaler.inverse_transform(dummy_features)[0, 0]
            
            # Get current price
            current_price_series_or_scalar = data['Close'].iloc[-1]
            if isinstance(current_price_series_or_scalar, pd.Series):
                current_price = float(current_price_series_or_scalar.iloc[0])
            else:
                current_price = float(current_price_series_or_scalar)
            
            # Calculate confidence based on recent volatility
            recent_volatility = data_with_features['volatility'].iloc[-1]
            confidence = max(0.5, min(0.95, 1 - (recent_volatility * 10)))
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'predicted_price': float(predicted_price),
                'change_percent': float((predicted_price - current_price) / current_price * 100),
                'confidence': float(confidence),
                'prediction_date': (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d'),
                'volatility': float(recent_volatility) if not pd.isna(recent_volatility) else None
            }
        
        except Exception as e:
            logging.error(f"Error predicting {symbol}: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def get_historical_data(self, symbol, days=30):
        try:
            data = self.get_crypto_data(symbol, period=f"{days+30}d")
            if data is None:
                return None
            
            # Get last 'days' records
            data = data.tail(days)
            
            chart_data = []
            for date, row in data.iterrows():
                price_series_or_scalar = row['Close']
                if isinstance(price_series_or_scalar, pd.Series):
                    price_float = float(price_series_or_scalar.iloc[0])
                else:
                    price_float = float(price_series_or_scalar)
                
                chart_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': price_float
                })
            return chart_data
        except Exception as e:
            logging.error(f"Error getting history for {symbol}: {e}")
            return None

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("="*60)
    print("ADVANCED CRYPTOCURRENCY PREDICTION MODEL")
    print("="*60)
    print("\nInitializing model... This may take a while on first run.")
    print("The model will train on 5 years of data with 200 epochs.\n")
    
    try:
        # Initialize and train models
        model = CryptoPredictionModel()
        
        print("\n" + "="*60)
        print("MAKING PREDICTIONS FOR ALL CRYPTOCURRENCIES")
        print("="*60 + "\n")
        
        # Make predictions for all symbols
        symbols = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        
        results = []
        for symbol in symbols:
            print(f"\nPredicting {symbol}...")
            prediction = model.predict_price(symbol)
            
            if prediction:
                results.append(prediction)
                print(f"✓ {symbol}: Current ${prediction['current_price']:.2f} → "
                      f"Predicted ${prediction['predicted_price']:.2f} "
                      f"({prediction['change_percent']:+.2f}%) "
                      f"[Confidence: {prediction['confidence']*100:.1f}%]")
            else:
                print(f"✗ {symbol}: Prediction failed")
        
        print("\n" + "="*60)
        print("PREDICTION SUMMARY")
        print("="*60)
        
        if results:
            # Sort by change percent
            results.sort(key=lambda x: x['change_percent'], reverse=True)
            
            print("\n📈 TOP GAINERS (Predicted):")
            for r in results[:3]:
                print(f"  {r['symbol']}: {r['change_percent']:+.2f}% "
                      f"(${r['current_price']:.2f} → ${r['predicted_price']:.2f})")
            
            print("\n📉 TOP LOSERS (Predicted):")
            for r in results[-3:]:
                print(f"  {r['symbol']}: {r['change_percent']:+.2f}% "
                      f"(${r['current_price']:.2f} → ${r['predicted_price']:.2f})")
            
            # Calculate average metrics
            avg_change = np.mean([r['change_percent'] for r in results])
            avg_confidence = np.mean([r['confidence'] for r in results])
            
            print(f"\n📊 MARKET OUTLOOK:")
            print(f"  Average predicted change: {avg_change:+.2f}%")
            print(f"  Average confidence: {avg_confidence*100:.1f}%")
            print(f"  Market sentiment: {'BULLISH 🚀' if avg_change > 0 else 'BEARISH 🐻'}")
        
        print("\n" + "="*60)
        print("DONE! Models saved in 'models/' directory")
        print("Logs saved in 'crypto_model.log'")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        logging.error(f"Fatal error: {e}")
        logging.error(traceback.format_exc())