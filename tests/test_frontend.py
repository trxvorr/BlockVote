import pytest
from app.node_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_frontend_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Cast Your Vote' in response.data

# We skip full vote submit test here as it requires a valid PEM key 
# which is cumbersome to generate in a simple request without wallet helper context.
# But we can verify it rejects missing params.
def test_frontend_submit_missing_params(client):
    response = client.post('/vote/submit', json={})
    assert response.status_code == 400

def test_admin_dashboard_loads(client):
    response = client.get('/admin')
    assert response.status_code == 200
    assert b'Admin Panel' in response.data

def test_candidates_api(client):
    # 1. Get empty list
    res = client.get('/candidates')
    assert res.status_code == 200
    assert res.json['candidates'] == []
    
    # 2. Add candidate
    res = client.post('/candidates/add', json={'name': 'Alice'})
    assert res.status_code == 201
    
    # 3. Get list again
    res = client.get('/candidates')
    assert 'Alice' in res.json['candidates']

def test_stats_endpoint(client):
    res = client.get('/stats')
    assert res.status_code == 200
    assert 'chain_length' in res.json
    assert 'nodes_count' in res.json
    assert res.json['chain_length'] >= 1  # At least genesis block
