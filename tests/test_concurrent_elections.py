import json
import os

import pytest

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

def test_concurrent_elections_voting(blockchain):
    # Election 1: "President"
    # Election 2: "Mayor"
    
    pub, priv = Wallet.generate_keys()
    
    # Vote for Alice for President
    tx1_data = {'sender': "voter1", 'recipient': "Alice", 'amount': 1, 'election_id': "President"}
    sig1 = Wallet.sign(json.dumps(tx1_data, sort_keys=True), priv)
    blockchain.new_transaction("voter1", "Alice", 1, sig1, pub, election_id="President")
    
    # Vote for Bob for Mayor
    tx2_data = {'sender': "voter1", 'recipient': "Bob", 'amount': 1, 'election_id': "Mayor"}
    sig2 = Wallet.sign(json.dumps(tx2_data, sort_keys=True), priv)
    blockchain.new_transaction("voter1", "Bob", 1, sig2, pub, election_id="Mayor")
    
    # Mine block
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    # Vote for Charlie for President
    tx3_data = {'sender': "voter2", 'recipient': "Charlie", 'amount': 1, 'election_id': "President"}
    sig3 = Wallet.sign(json.dumps(tx3_data, sort_keys=True), priv)
    blockchain.new_transaction("voter2", "Charlie", 1, sig3, pub, election_id="President")
    
    # Mine block
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    # Count votes
    results = blockchain.count_votes()
    
    # Verify separation
    assert "President" in results
    assert "Mayor" in results
    
    assert results["President"]["Alice"] == 1
    assert results["President"]["Charlie"] == 1
    assert results["Mayor"]["Bob"] == 1
    
    # Verify no cross-contamination
    assert "Bob" not in results["President"]
    assert "Alice" not in results["Mayor"]
