-----

# 🚀 Crypto Price Predictor AI: Hybrid Intelligence Dashboard

### Bridging the gap between Raw Data and Actionable Financial Insights.

-----

## 🧠 The Core Innovation: Hybrid AI System

This project utilizes a dual-AI architecture to deliver superior results:

### 1\. The Quant (Predictive AI) 📈

A custom-built **Stacked LSTM (Long Short-Term Memory)** Neural Network.

  * **Training:** Trained on **3 years** of historical data.
  * **Logic:** Predicts the **next day's closing price** based on complex 60-day temporal patterns.

### 2\. The Analyst (Generative AI) 🤖

Integration with **GPT-4o** (via Bytez).

  * **Function:** Interprets the numerical prediction.
  * **Output:** Generates a **human-readable, context-aware market analysis** (e.g., "Bullish trend detected").

-----

## ✨ Key Features

### 🔮 Advanced AI Prediction Engine

  * **Model Architecture:** 4-Layer Stacked LSTM with Dropout Regularization.
  * **Data Pipeline:** Real-time data fetching via Yahoo Finance (`yfinance`).
  * **Supported Assets:** Real-time predictions for **8 Major Cryptocurrencies**:
      * `BTC`, `ETH`, `ADA`, `SOL`, `DOT`, `AVAX`, `LINK`, `LTC`

### 📊 Interactive Dashboard

  * **Live Charts:** Dynamic `Chart.js` visualizations (7D, 30D, 90D views).
  * **Glassmorphism UI:** Modern interface built with **Tailwind CSS**.
  * **Theme Aware:** Fully functional **Dark Mode 🌙** and **Light Mode ☀️**.

### 💼 Portfolio Tracker

  * **Real-time P\&L:** Track personal crypto holdings with live profit/loss updates.
  * **Persistent Storage:** Uses **SQLite** to safely store user portfolios.

-----

## 🏗️ Technical Architecture

The application follows a robust 3-tier architecture:

1.  **Frontend:** HTML5, Tailwind CSS, Vanilla JS.
2.  **Backend:** Flask (Python) serving RESTful APIs.
3.  **AI Layer:** TensorFlow (Inference) + OpenAI (Analysis).

<!-- end list -->

```
crypto-price-predictor-ai/
│
├── app.py                  # Application Entry Point
├── ml_model.py             # THE BRAIN: LSTM Architecture
├── routes.py               # THE WAITER: API Endpoints
│
├── models/                 # Pre-trained LSTM Models (.keras)
├── scalers/                # Saved Data Scalers (.pkl)
│
├── templates/              # Frontend UI
└── static/                 # CSS & JavaScript
```

-----

## 🚀 Quick Start Guide

### 1\. Clone the Repository

```bash
git clone <your-repo-url>
cd crypto-price-predictor-ai
```

### 2\. Set up Virtual Environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate
```

### 3\. Install Dependencies

```bash
pip install flask flask-sqlalchemy flask-cors numpy pandas yfinance tensorflow bytez
```

### 4\. Initialize Database

```bash
python
>>> from app import app, db
>>> with app.app_context(): db.create_all()
>>> exit()
```

### 5\. Train Models (First Run Only)

```bash
# This trains the LSTM models and saves them to /models
python train_model.py
```

### 6\. Run the App

```bash
python -m flask run --host=0.0.0.0 --port=5000
```

-----

## 🤖 Model Technical Details

| Parameter | Value |
| :--- | :--- |
| **Algorithm** | Long Short-Term Memory (LSTM) |
| **Training Data** | 3 Years (Daily Closing Prices) |
| **Lookback Window** | 60 Days |
| **Loss Function** | Mean Squared Error (MSE) |
| **Optimizer** | Adam |
| **Epochs** | 25 |

-----

## 🔮 Roadmap & Future Enhancements

  * [ ] **Automated Retraining Pipeline:** Nightly Cron Job to retrain models.
  * [ ] **Multi-Feature Input:** Add Volume, Open, High, Low data.
  * [ ] **User Accounts:** Secure login/signup.
  * [ ] **Sentiment Analysis:** Integrate News API.

-----

### 📄 License

This project is built for **educational and competition purposes**.

**Built with ❤️ using Flask, TensorFlow, and OpenAI**
