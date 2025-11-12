# Overview

Crypto Price Predictor AI is a full-stack web application that uses machine learning to predict cryptocurrency prices. The application features a modern React-based frontend with glassmorphism design, a Flask REST API backend, and a Linear Regression ML model for price predictions. Users can select between Bitcoin (BTC) and Ethereum (ETH) to generate next-day price predictions, with all predictions stored in a database for historical tracking.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: React.js with Tailwind CSS for styling
- **Design Pattern**: Single Page Application (SPA) with component-based architecture
- **UI/UX**: Modern glassmorphism design with dark mode support and responsive layout
- **Charting**: Chart.js integration for displaying prediction results and historical data
- **State Management**: Vanilla JavaScript class-based approach for application state

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM for database operations
- **API Design**: RESTful API with JSON responses
- **Database Layer**: SQLAlchemy with support for both PostgreSQL and SQLite
- **ML Integration**: scikit-learn Linear Regression model with Yahoo Finance data integration
- **Error Handling**: Comprehensive logging and error responses

## Data Storage
- **Primary Database**: PostgreSQL (production) with SQLite fallback (development)
- **ORM**: SQLAlchemy with DeclarativeBase for model definitions
- **Schema**: Single Prediction model storing crypto symbol, predicted prices, actual prices, and timestamps
- **Connection Management**: Pool recycling and pre-ping health checks for database reliability

## Machine Learning Pipeline
- **Algorithm**: Linear Regression using scikit-learn
- **Data Source**: Yahoo Finance API via yfinance library
- **Feature Engineering**: Lookback window approach using past N days of closing prices
- **Model Management**: In-memory model storage with automatic training and persistence
- **Prediction Scope**: Next-day price predictions for BTC and ETH

## Authentication & Security
- **Session Management**: Flask session handling with configurable secret keys
- **CORS**: Enabled for cross-origin requests
- **Environment Configuration**: Environment-based configuration for database URLs and secrets

# External Dependencies

## Third-Party APIs
- **Yahoo Finance**: Real-time and historical cryptocurrency price data via yfinance library
- **Data Coverage**: BTC-USD and ETH-USD trading pairs with 1-year historical data

## Python Libraries
- **Web Framework**: Flask, Flask-SQLAlchemy, Flask-CORS
- **Machine Learning**: scikit-learn, numpy, pandas
- **Data Fetching**: yfinance for Yahoo Finance API integration
- **Database**: SQLAlchemy with PostgreSQL/SQLite support

## Frontend Libraries
- **Styling**: Tailwind CSS via CDN
- **Charting**: Chart.js for data visualization
- **Icons**: Feather Icons for UI elements

## Database Systems
- **Primary**: PostgreSQL for production environments
- **Fallback**: SQLite for development and testing
- **Connection**: Environment-based URL configuration with automatic PostgreSQL URL formatting