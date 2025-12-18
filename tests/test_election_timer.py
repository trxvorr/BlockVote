import pytest
import time
import json
import os
from app.blockchain import Blockchain
from app.wallet import Wallet

TEST_PORT = 9999
DATA_DIR = 'data'
FILE_PATH = f'{DATA_DIR}/chain_{TEST_PORT}.json'

@pytest.fixture
def blockchain():
    # Cleanup before
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
        
    bc = Blockchain(port=TEST_PORT)
    yield bc
    
    # Cleanup after
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

def test_election_window_not_set(blockchain):
    # Should allow voting
    pub, priv = Wallet.generate_keys()
    sig = Wallet.sign(json.dumps({'sender': "s", 'recipient': "r", 'amount': 1}, sort_keys=True), priv)
    blockchain.new_transaction("s", "r", 1, sig, pub)
    assert len(blockchain.current_transactions) == 1

def test_vote_before_election_start(blockchain):
    pub, priv = Wallet.generate_keys()
    sig = Wallet.sign(json.dumps({'sender': "s", 'recipient': "r", 'amount': 1}, sort_keys=True), priv)
    
    # Set window to start in 1 hour
    now = time.time()
    blockchain.set_election_window(now + 3600, now + 7200)
    
    with pytest.raises(ValueError) as exc:
        blockchain.new_transaction("s", "r", 1, sig, pub)
    
    assert "Election has not started yet" in str(exc.value)

def test_vote_after_election_end(blockchain):
    pub, priv = Wallet.generate_keys()
    sig = Wallet.sign(json.dumps({'sender': "s", 'recipient': "r", 'amount': 1}, sort_keys=True), priv)
    
    # Set window ending 1 hour ago
    now = time.time()
    blockchain.set_election_window(now - 7200, now - 3600)
    
    with pytest.raises(ValueError) as exc:
        blockchain.new_transaction("s", "r", 1, sig, pub)
    
    assert "Election has ended" in str(exc.value)

def test_vote_during_election(blockchain):
    pub, priv = Wallet.generate_keys()
    sig = Wallet.sign(json.dumps({'sender': "s", 'recipient': "r", 'amount': 1}, sort_keys=True), priv)
    
    # Set window surrounding now
    now = time.time()
    blockchain.set_election_window(now - 100, now + 100)
    
    blockchain.new_transaction("s", "r", 1, sig, pub)
    assert len(blockchain.current_transactions) == 1

def test_mining_ignores_timer(blockchain):
    # Set window ending 1 hour ago (voting closed)
    now = time.time()
    blockchain.set_election_window(now - 7200, now - 3600)
    
    # Mining reward sender='0' should bypass check
    blockchain.new_transaction("0", "miner", 1)
    assert len(blockchain.current_transactions) == 1
