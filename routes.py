from flask import render_template, request, jsonify
from app import app, db
from models import Prediction
from datetime import datetime
import logging

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
