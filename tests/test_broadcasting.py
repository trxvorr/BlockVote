import pytest
import json
from unittest.mock import patch, MagicMock
from app.node_server import app
from app.wallet import Wallet

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_transaction_broadcasting(client):
    # Setup keys
    pub, priv = Wallet.generate_keys()
    sender = "sender"
    recipient = "recipient"
    amount = 100
    message = json.dumps({'sender': sender, 'recipient': recipient, 'amount': amount}, sort_keys=True)
    signature = Wallet.sign(message, priv).hex()
    
    # Mock requests.post
    with patch('requests.post') as mock_post:
        # Create Payload
        payload = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': signature,
            'public_key': pub.decode()
        }
        
        # Add a node to broadcast to
        from app.node_server import blockchain
        blockchain.nodes.add("peer-node:5000")
        
        # 1. Post NEW transaction
        # Mock Thread to avoid actual spawning
        with patch('threading.Thread') as mock_thread:
            response = client.post('/transactions/new', json=payload)
            assert response.status_code == 201
            # Verify thread started
            mock_thread.assert_called_once()
        
        # 2. Post DUPLICATE transaction
        # Should return 200 and NOT start thread
        with patch('threading.Thread') as mock_thread_dup:
             response = client.post('/transactions/new', json=payload)
             assert response.status_code == 200
             assert "already exists" in response.get_json()['message']
             
             mock_thread_dup.assert_not_called()

