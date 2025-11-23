🚀 Crypto Price Predictor AI: Hybrid Intelligence Dashboard
A comprehensive full-stack web application that combines Deep Learning (LSTM) for price forecasting with Generative AI (GPT-4o) for market analysis. It bridges the gap between raw data and actionable financial insights.

🧠 The Core Innovation: Hybrid AI System
This project is not just a price tracker. It utilizes a dual-AI architecture:

The Quant (Predictive AI): A custom-built Stacked LSTM (Long Short-Term Memory) Neural Network trained on 3 years of historical data to predict the next day's closing price based on 60-day temporal patterns.

The Analyst (Generative AI): Integration with GPT-4o (via Bytez) to interpret the numerical prediction and generate a human-readable, context-aware market analysis.

✨ Key Features
🔮 Advanced AI Prediction Engine
Model Architecture: 4-Layer Stacked LSTM with Dropout Regularization to prevent overfitting.

Data Pipeline: Real-time data fetching via Yahoo Finance (yfinance) with a 60-day lookback window.

Supported Assets: Real-time predictions for 8 major cryptocurrencies: BTC, ETH, ADA, SOL, DOT, AVAX, LINK, LTC.

Smart Pre-processing: Automated MinMax scaling and 3D data reshaping for neural network ingestion.

🤖 AI Market Analyst
Automated Insights: Converts complex price predictions into simple, beginner-friendly market summaries.

Sentiment Analysis: Automatically identifies "Bullish" or "Bearish" trends based on the model's forecast.

📊 Interactive Dashboard
Live Charts: Dynamic Chart.js visualizations showing historical price action (7D, 30D, 90D).

Glassmorphism UI: A modern, aesthetically pleasing interface built with Tailwind CSS.

Theme Aware: Fully functional Dark Mode and Light Mode with high-contrast visibility.

💼 Portfolio Tracker
Real-time P&L: Track personal crypto holdings with live profit/loss calculations.

Persistent Storage: Uses SQLite (scalable to PostgreSQL) to save user portfolios and prediction history.

🏗️ Technical Architecture
The application follows a robust 3-tier architecture:

Frontend: HTML5, Tailwind CSS, Vanilla JS (Handles UI logic and async API calls).

Backend: Flask (Python) serving RESTful APIs.

AI Layer:Inference Engine: TensorFlow/Keras (Loads pre-trained .keras models).

Analysis Engine: Bytez SDK (Connects to OpenAI GPT-4o).

crypto-price-predictor-ai/
│
├── app.py                  # Application entry point & Config
├── ml_model.py             # THE BRAIN: LSTM Architecture, Training, & Prediction Logic
├── routes.py               # API Endpoints (Predict, Analyze, History)
├── models.py               # Database Schema
│
├── models/                 # Pre-trained LSTM Models (.keras files)
├── scalers/                # Saved Data Scalers (.pkl files)
│
├── templates/
│   └── index.html          # Main Dashboard
└── static/
    └── js/
        └── app.js          # Frontend Logic (API integration)

        🚀 Quick Start
Prerequisites
Python 3.10+

Virtual Environment (Recommended)

Installation
Clone the repository

Bash

git clone <your-repo-url>
cd crypto-price-predictor-ai
Set up Virtual Environment

Bash

python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
Install Dependencies

Bash

pip install flask flask-sqlalchemy flask-cors numpy pandas yfinance tensorflow bytez
Initialize Database

Bash

python
>>> from app import app, db
>>> with app.app_context(): db.create_all()
>>> exit()
Train/Load Models (First run only)

Bash

# This trains the LSTM models and saves them to /models
python train_model.py
Run the Application

Bash

python -m flask run --host=0.0.0.0 --port=5000
🤖 Model Technical Details
Algorithm: Long Short-Term Memory (LSTM) Recurrent Neural Network.

Training Data: 3 Years of Daily Closing Prices (OHLCV).

Input Shape: (Samples, 60, 1) - The model looks at a sequence of the past 60 days.

Loss Function: Mean Squared Error (MSE) - Optimized to penalize large prediction errors.

Optimizer: Adam.

Training Epochs: 25 (with Early Stopping logic capabilities).

🔮 Roadmap & Future Enhancements
[ ] Automated Retraining Pipeline: Implement a Cron Job to retrain LSTM models nightly with the latest data to prevent model staleness.

[ ] Multi-Feature Input: Expand LSTM to use Volume, Open, High, and Low prices (multivariate) for higher accuracy.

[ ] User Accounts: Implement secure login/signup for personalized portfolios.

[ ] Sentiment Analysis: Integrate news API to feed social sentiment into the LSTM model.

📄 License
This project is built for educational and competition purposes.

Built with ❤️ using Flask, TensorFlow, and OpenAI

Inference Engine: TensorFlow/Keras (Loads pre-trained .keras models).

Analysis Engine: Bytez SDK (Connects to OpenAI GPT-4o).
