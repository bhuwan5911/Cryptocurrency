from flask import render_template, request, jsonify
from app import app, db
from models import Prediction, PortfolioHolding
from datetime import datetime
import logging
import yfinance as yf

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Generate price prediction for selected cryptocurrency"""
    try:
        data = request.get_json()
        crypto = data.get('crypto', '').upper()
        
        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'AVAX', 'LINK', 'UNI', 'LTC']
        if crypto not in valid_cryptos:
            return jsonify({'error': f'Invalid cryptocurrency. Please select from: {", ".join(valid_cryptos)}.'}), 400
        
        # Generate prediction using ML model
        prediction_result = app.ml_model.predict_price(crypto)
        
        if not prediction_result:
            return jsonify({'error': f'Failed to generate prediction for {crypto}. Please try again.'}), 500
        
        # Save prediction to database
        prediction = Prediction(
            crypto=crypto,
            predicted_price=prediction_result['predicted_price'],
            prediction_date=prediction_result['prediction_date']
        )
        
        db.session.add(prediction)
        db.session.commit()
        
        # Return prediction with additional info
        response_data = {
            'success': True,
            'crypto': crypto,
            'current_price': prediction_result['current_price'],
            'predicted_price': prediction_result['predicted_price'],
            'change_percent': prediction_result['change_percent'],
            'prediction_date': prediction_result['prediction_date'],
            'prediction_id': prediction.id
        }
        
        logging.info(f"Generated prediction for {crypto}: ${prediction_result['predicted_price']:.2f}")
        return jsonify(response_data)
    
    except Exception as e:
        logging.error(f"Error in predict endpoint: {e}")
        return jsonify({'error': 'An error occurred while generating the prediction.'}), 500

@app.route('/api/history')
def history():
    """Get historical predictions"""
    try:
        # Get last 7 predictions
        predictions = Prediction.query.order_by(Prediction.date.desc()).limit(7).all()
        
        if not predictions:
            return jsonify({
                'success': True,
                'predictions': [],
                'message': 'No predictions found. Make your first prediction!'
            })
        
        predictions_data = [pred.to_dict() for pred in predictions]
        
        return jsonify({
            'success': True,
            'predictions': predictions_data
        })
    
    except Exception as e:
        logging.error(f"Error in history endpoint: {e}")
        return jsonify({'error': 'Failed to retrieve prediction history.'}), 500

@app.route('/api/chart-data')
def chart_data():
    """Get historical price data for charts"""
    try:
        crypto = request.args.get('crypto', 'BTC').upper()
        days = request.args.get('days', 30, type=int)
        
        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'AVAX', 'LINK', 'UNI', 'LTC']
        if crypto not in valid_cryptos:
            return jsonify({'error': 'Invalid cryptocurrency'}), 400
        
        # Get historical data
        historical_data = app.ml_model.get_historical_data(crypto, days)
        
        if not historical_data:
            return jsonify({'error': f'Failed to get historical data for {crypto}'}), 500
        
        return jsonify({
            'success': True,
            'crypto': crypto,
            'data': historical_data
        })
    
    except Exception as e:
        logging.error(f"Error in chart-data endpoint: {e}")
        return jsonify({'error': 'Failed to retrieve chart data.'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error occurred.'}), 500

# Portfolio Management Endpoints
@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get all portfolio holdings with current values"""
    try:
        holdings = PortfolioHolding.query.order_by(PortfolioHolding.created_at.desc()).all()
        
        if not holdings:
            return jsonify({
                'success': True,
                'holdings': [],
                'total_value': 0,
                'total_invested': 0,
                'total_pnl': 0,
                'total_pnl_percent': 0
            })
        
        # Get current prices for all unique cryptos in portfolio
        cryptos = list(set([h.crypto for h in holdings]))
        current_prices = {}
        
        for crypto in cryptos:
            try:
                ticker = yf.Ticker(f"{crypto}-USD")
                data = ticker.history(period="1d")
                if not data.empty:
                    current_prices[crypto] = float(data['Close'].iloc[-1])
            except:
                current_prices[crypto] = 0
        
        # Calculate portfolio metrics
        holdings_data = []
        total_value = 0
        total_invested = 0
        
        for holding in holdings:
            current_price = current_prices.get(holding.crypto, 0)
            current_value = holding.amount * current_price
            invested_value = holding.amount * holding.purchase_price
            pnl = current_value - invested_value
            pnl_percent = (pnl / invested_value * 100) if invested_value > 0 else 0
            
            holding_data = holding.to_dict()
            holding_data.update({
                'current_price': round(current_price, 2),
                'current_value': round(current_value, 2),
                'invested_value': round(invested_value, 2),
                'pnl': round(pnl, 2),
                'pnl_percent': round(pnl_percent, 2)
            })
            
            holdings_data.append(holding_data)
            total_value += current_value
            total_invested += invested_value
        
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        return jsonify({
            'success': True,
            'holdings': holdings_data,
            'total_value': round(total_value, 2),
            'total_invested': round(total_invested, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_percent': round(total_pnl_percent, 2)
        })
        
    except Exception as e:
        logging.error(f"Error getting portfolio: {e}")
        return jsonify({'error': 'Failed to load portfolio'}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_holding():
    """Add a new portfolio holding"""
    try:
        data = request.get_json()
        crypto = data.get('crypto', '').upper()
        amount = float(data.get('amount', 0))
        purchase_price = float(data.get('purchase_price', 0))
        notes = data.get('notes', '')
        
        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'MATIC', 'DOT', 'AVAX', 'LINK', 'UNI', 'LTC']
        if crypto not in valid_cryptos:
            return jsonify({'error': f'Invalid cryptocurrency. Please select from: {", ".join(valid_cryptos)}.'}), 400
        
        if amount <= 0 or purchase_price <= 0:
            return jsonify({'error': 'Amount and purchase price must be greater than 0.'}), 400
        
        # Create new holding
        holding = PortfolioHolding(
            crypto=crypto,
            amount=amount,
            purchase_price=purchase_price,
            notes=notes
        )
        
        db.session.add(holding)
        db.session.commit()
        
        logging.info(f"Added portfolio holding: {amount} {crypto} @ ${purchase_price}")
        return jsonify({
            'success': True,
            'message': f'Added {amount} {crypto} to your portfolio',
            'holding': holding.to_dict()
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid amount or price format.'}), 400
    except Exception as e:
        logging.error(f"Error adding holding: {e}")
        return jsonify({'error': 'Failed to add holding to portfolio'}), 500

@app.route('/api/portfolio/<int:holding_id>', methods=['DELETE'])
def delete_holding(holding_id):
    """Delete a portfolio holding"""
    try:
        holding = PortfolioHolding.query.get_or_404(holding_id)
        crypto_name = holding.crypto
        
        db.session.delete(holding)
        db.session.commit()
        
        logging.info(f"Deleted portfolio holding: {crypto_name}")
        return jsonify({
            'success': True,
            'message': f'Removed {crypto_name} from your portfolio'
        })
        
    except Exception as e:
        logging.error(f"Error deleting holding: {e}")
        return jsonify({'error': 'Failed to remove holding from portfolio'}), 500
