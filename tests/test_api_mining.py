import json

import pytest

from app.node_server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_full_chain(client):
    response = client.get('/chain')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'chain' in data
    assert 'length' in data
    assert data['length'] >= 1  # Genesis block

def test_mine(client):
    # This might take a second due to PoW
    response = client.get('/mine')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['message'] == "New Block Forged"
    assert 'index' in data
    assert 'transactions' in data
    assert 'proof' in data
    assert 'previous_hash' in data
    
    # Verify transaction reward
    txs = data['transactions']
    assert len(txs) > 0
    assert txs[-1]['sender'] == "0"
    assert txs[-1]['amount'] == 1
