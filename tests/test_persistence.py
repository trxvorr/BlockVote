import pytest
import os
import json
import shutil
from app.blockchain import Blockchain

TEST_PORT = 9999
DATA_DIR = 'data'
FILE_PATH = f'{DATA_DIR}/chain_{TEST_PORT}.json'

@pytest.fixture
def clean_persistence():
    # Setup: Remove test file if exists
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    yield
    # Teardown: Remove test file
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

def test_save_and_load_state(clean_persistence):
    # 1. Start clean blockchain
    bc = Blockchain(port=TEST_PORT)
    assert len(bc.chain) == 1 # Genesis
    
    # 2. Add data
    from app.wallet import Wallet
    pub, priv = Wallet.generate_keys()
    
    sender = "sender"
    recipient = "recipient"
    amount = 100
    
    message = json.dumps({'sender': sender, 'recipient': recipient, 'amount': amount}, sort_keys=True)
    signature = Wallet.sign(message, priv)
    
    bc.nodes.add("http://127.0.0.1:8000")
    bc.new_transaction(sender, recipient, amount, signature, pub)
    bc.new_block(proof=123, previous_hash='abc')
    
    assert len(bc.chain) == 2
    assert len(bc.nodes) == 1
    
    # 3. Blockchain saves automatically on changes. 
    # Check file exists and has content
    assert os.path.exists(FILE_PATH)
    with open(FILE_PATH, 'r') as f:
        data = json.load(f)
        assert len(data['chain']) == 2
        assert len(data['nodes']) == 1
    
    # 4. "Restart" blockchain (create new instance)
    bc2 = Blockchain(port=TEST_PORT)
    
    # 5. Verify state loaded
    assert len(bc2.chain) == 2
    assert len(bc2.nodes) == 1
    assert "http://127.0.0.1:8000" in bc2.nodes
    assert bc2.chain[-1]['proof'] == 123

def test_initial_load_failure_creates_genesis(clean_persistence):
    # If no file, starts with genesis
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
        
    bc = Blockchain(port=TEST_PORT)
    assert len(bc.chain) == 1
    assert bc.chain[0]['proof'] == 100
