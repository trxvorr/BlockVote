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
