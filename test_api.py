import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
    # Checking if HTML content is returned
    assert b'<!DOCTYPE html>' in rv.data or b'<html' in rv.data

def test_predict_valid_crypto(client):
    rv = client.post('/api/predict', json={"crypto": "BTC"})
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert 'success' in json_data
    # success may be True or False depending on model availability
    assert 'crypto' in json_data or 'error' in json_data

def test_predict_invalid_crypto(client):
    rv = client.post('/api/predict', json={"crypto": "INVALID"})
    assert rv.status_code == 400
    json_data = rv.get_json()
    assert 'error' in json_data

def test_api_history(client):
    rv = client.get('/api/history')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert 'success' in json_data and 'predictions' in json_data

def test_api_chart_data_valid(client):
    rv = client.get('/api/chart-data?crypto=BTC&days=10')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert 'success' in json_data and 'data' in json_data

def test_api_chart_data_invalid(client):
    rv = client.get('/api/chart-data?crypto=INVALID&days=10')
    assert rv.status_code == 400
    json_data = rv.get_json()
    assert 'error' in json_data
