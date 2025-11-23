# routes.py
from flask import render_template, request, jsonify
from app import app, db
from models import Prediction, PortfolioHolding
from datetime import datetime
import logging
import yfinance as yf
import os

# -------------------------
# Helper: simple local analyzer (fallback)
# -------------------------
def simple_local_analysis(crypto: str, current_price: float, predicted_price: float) -> str:
    """
    Short, neutral beginner-friendly analysis.
    This is a non-AI fallback so the endpoint works even if Bytez isn't installed.
    """
    try:
        current_price = float(current_price)
        predicted_price = float(predicted_price)
        if current_price <= 0:
            return "Insufficient price data to analyze."
        change = (predicted_price - current_price) / current_price * 100.0

        if change > 2.0:
            sentiment = "bullish"
            note = "The prediction indicates mildly positive short-term sentiment."
        elif change < -2.0:
            sentiment = "bearish"
            note = "The prediction indicates mildly negative short-term sentiment."
        else:
            sentiment = "neutral"
            note = "The prediction suggests little short-term change."

        # Keep this short, neutral and NOT financial advice
        return f"This looks {sentiment}. {note} (Forecast delta: {change:.2f}%)."
    except Exception as e:
        logging.exception("Error in simple_local_analysis")
        return "Could not generate local analysis."

# -------------------------
# Analyze route (uses Bytez if available, otherwise fallback)
# -------------------------
@app.route('/api/analyze', methods=['POST'])
def analyze_prediction():
    """
    Analyze prediction using Bytez SDK if installed.
    If Bytez is not installed or fails, use simple_local_analysis fallback.
    This design prevents ModuleNotFoundError at import time.
    """
    try:
        data = request.get_json(force=True)
        crypto = data.get('crypto')
        current_price = data.get('current_price')
        predicted_price = data.get('predicted_price')

        if not all([crypto, current_price, predicted_price]):
            return jsonify({'error': 'Missing data for analysis'}), 400

        # Attempt to import Bytez lazily (inside the route)
        try:
            from bytez import Bytez  # try import here so app import won't fail if package missing
            bytez_key = os.environ.get("BYTEZ_API_KEY", "63ce62411ba8cdbcb13b0674b44c480e")
            sdk = Bytez(bytez_key)
            ai_analyst_model = sdk.model("openai/gpt-4o-mini")
            logging.info("Bytez SDK loaded inside analyze_prediction.")
        except Exception as imp_exc:
            ai_analyst_model = None
            logging.warning(f"Bytez SDK not available or failed to initialize: {imp_exc}. Using fallback analyzer.")

        # If Bytez is available, try calling it. Keep robust handling for different return shapes.
        if ai_analyst_model is not None:
            prompt_to_ai = f"""
You are a neutral crypto market analyst.
A user's LSTM AI model predicts that {crypto} will go from ${float(current_price):,.2f} to ${float(predicted_price):,.2f} tomorrow.

Write a very short, 2-3 sentence analysis for a beginner.
- Is this a "bullish" (positive) or "bearish" (negative) signal?
- What does this suggest about the short-term market sentiment?

IMPORTANT: Do NOT give financial advice. Do NOT tell the user to 'buy', 'sell', or 'hold'.
Just analyze the model's prediction in simple terms.
"""
            messages = [
                {"role": "system", "content": "You are a helpful crypto analyst who speaks in simple terms."},
                {"role": "user", "content": prompt_to_ai}
            ]

            try:
                run_response = ai_analyst_model.run(messages)
                # handle common shapes: (output, error), list/tuple, or dict/string
                error = None
                output = None
                if isinstance(run_response, (list, tuple)):
                    if len(run_response) >= 1:
                        output = run_response[0]
                    if len(run_response) >= 2:
                        error = run_response[1]
                elif isinstance(run_response, dict):
                    output = run_response
                else:
                    output = run_response

                if error:
                    logging.error(f"Bytez returned an error: {error}")
                    raise Exception(error)

                # extract content safely
                if isinstance(output, dict) and 'content' in output:
                    analysis_text = output['content']
                else:
                    analysis_text = str(output)

                logging.info(f"AI Analysis generated for {crypto} using Bytez.")
                return jsonify({'success': True, 'analysis': analysis_text})
            except Exception as e:
                logging.exception("Bytez call failed; falling back to local analysis.")
                analysis_text = simple_local_analysis(crypto, current_price, predicted_price)
                return jsonify({'success': True, 'analysis': analysis_text, 'note': 'Used local fallback because Bytez failed.'})

        # If Bytez not available, use the fallback
        analysis_text = simple_local_analysis(crypto, current_price, predicted_price)
        return jsonify({'success': True, 'analysis': analysis_text, 'note': 'Bytez SDK not installed; used local fallback.'})

    except Exception as e:
        logging.exception("Error in /api/analyze endpoint")
        return jsonify({'error': 'Failed to generate AI analysis.'}), 500

# -------------------------
# The rest of your routes below (unchanged)
# -------------------------
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Generate price prediction for selected cryptocurrency"""
    try:
        data = request.get_json(force=True)
        crypto = data.get('crypto', '').upper()

        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        if crypto not in valid_cryptos:
            return jsonify({'error': f'Invalid cryptocurrency.'}), 400

        prediction_result = app.ml_model.predict_price(crypto)

        if not prediction_result:
            return jsonify({'error': f'Failed to generate prediction for {crypto}. Please try again.'}), 500

        prediction = Prediction(
            crypto=crypto,
            predicted_price=prediction_result['predicted_price'],
            actual_price=None,
            prediction_date=datetime.strptime(prediction_result['prediction_date'], '%Y-%m-%d').date()
        )

        db.session.add(prediction)
        db.session.commit()

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
        logging.exception("Error in predict endpoint")
        return jsonify({'error': 'An error occurred while generating the prediction.'}), 500

@app.route('/api/history')
def history():
    """Get historical predictions"""
    try:
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
        logging.exception("Error in history endpoint")
        return jsonify({'error': 'Failed to retrieve prediction history.'}), 500

@app.route('/api/chart-data')
def chart_data():
    """Get historical price data for charts"""
    try:
        crypto = request.args.get('crypto', 'BTC').upper()
        days = request.args.get('days', 30, type=int)

        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        if crypto not in valid_cryptos:
            return jsonify({'error': 'Invalid cryptocurrency'}), 400

        historical_data = app.ml_model.get_historical_data(crypto, days)

        if not historical_data:
            return jsonify({'error': f'Failed to get historical data for {crypto}'}), 500

        return jsonify({
            'success': True,
            'crypto': crypto,
            'data': historical_data
        })

    except Exception as e:
        logging.exception("Error in chart-data endpoint")
        return jsonify({'error': 'Failed to retrieve chart data.'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error occurred.'}), 500

# Portfolio routes
@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get all portfolio holdings with current values"""
    try:
        holdings = PortfolioHolding.query.order_by(PortfolioHolding.created_at.desc()).all()

        if not holdings:
            return jsonify({
                'success': True,
                'holdings': [], 'total_value': 0, 'total_invested': 0,
                'total_pnl': 0, 'total_pnl_percent': 0
            })

        cryptos = list(set([h.crypto for h in holdings]))
        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        cryptos = [c for c in cryptos if c in valid_cryptos]

        current_prices = {}
        for crypto in cryptos:
            try:
                ticker = yf.Ticker(f"{crypto}-USD")
                data = ticker.history(period="1d")
                if not data.empty:
                    current_prices[crypto] = float(data['Close'].iloc[-1])
            except Exception:
                current_prices[crypto] = 0

        holdings_data = []
        total_value = 0
        total_invested = 0

        for holding in holdings:
            current_price = current_prices.get(holding.crypto, 0)
            current_value = (holding.amount or 0) * current_price
            invested_value = (holding.amount or 0) * (holding.purchase_price or 0)
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
        logging.exception("Error getting portfolio")
        return jsonify({'error': 'Failed to load portfolio'}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_holding():
    """Add a new portfolio holding"""
    try:
        data = request.get_json(force=True)
        crypto = data.get('crypto', '').upper()
        amount = float(data.get('amount', 0))
        purchase_price = float(data.get('purchase_price', 0))
        notes = data.get('notes', '')

        valid_cryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'LINK', 'LTC']
        if crypto not in valid_cryptos:
            return jsonify({'error': 'Invalid cryptocurrency.'}), 400

        if amount <= 0 or purchase_price <= 0:
            return jsonify({'error': 'Amount and purchase price must be greater than 0.'}), 400

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
        logging.exception("Error adding holding")
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
        logging.exception("Error deleting holding")
        return jsonify({'error': 'Failed to remove holding from portfolio'}), 500
