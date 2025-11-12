#!/usr/bin/env python3
"""
Script to train and save ML models for crypto prediction
Run this script to initialize or retrain models
"""

from ml_model import CryptoPredictionModel
import logging

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting model training...")
    
    # Initialize and train models
    predictor = CryptoPredictionModel()
    
    # Test predictions
    for symbol in ['BTC', 'ETH']:
        prediction = predictor.predict_price(symbol)
        if prediction:
            print(f"\n{symbol} Prediction:")
            print(f"Current Price: ${prediction['current_price']:.2f}")
            print(f"Predicted Price: ${prediction['predicted_price']:.2f}")
            print(f"Change: {prediction['change_percent']:.2f}%")
        else:
            print(f"Failed to generate prediction for {symbol}")
    
    logging.info("Model training completed!")

if __name__ == "__main__":
    main()
