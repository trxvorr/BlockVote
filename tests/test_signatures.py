import pytest
import json
import os
from app.blockchain import Blockchain
from app.wallet import Wallet

TEST_PORT = 9991
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

def test_signed_transaction_success(blockchain):
    # 1. Generate keys
    pub, priv = Wallet.generate_keys()
    
    # 2. Create Transaction Data
    sender = "sender_address"
    recipient = "recipient_address"
    amount = 5
    
    # Sign message
    # Updated: Must include 'election_id' or match what new_transaction expects
    # new_transaction defaults election_id='default', so we must sign that.
    transaction_data = {
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'election_id': 'default'
    }
    message = json.dumps(transaction_data, sort_keys=True)
    
    # 3. Sign
    signature = Wallet.sign(message, priv)
    
    # 4. Submit
    idx, _ = blockchain.new_transaction(sender, recipient, amount, signature, pub)
    assert idx == 2  # Genesis block is 1

def test_signed_transaction_invalid_signature(blockchain):
    pub, priv = Wallet.generate_keys()
    sender = "sender_address"
    recipient = "recipient_address"
    amount = 5
    
    # Sign WRONG message
    signature = Wallet.sign("wrong message", priv)
    
    with pytest.raises(ValueError) as excinfo:
        blockchain.new_transaction(sender, recipient, amount, signature, pub)
    
    assert "Invalid Transaction Signature" in str(excinfo.value)

def test_signed_transaction_missing_signature(blockchain):
    with pytest.raises(ValueError):
        blockchain.new_transaction("sender", "recipient", 5)

def test_mining_reward_skip(blockchain):
    # Sender '0' indicates mining reward, should skip sig check
    idx, _ = blockchain.new_transaction("0", "recipient_miner", 1)
    assert idx == 2
