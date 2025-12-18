import pytest
import os
from app.blockchain import Blockchain

TEST_PORT = 9996
DATA_DIR = 'data'
FILE_PATH = f'{DATA_DIR}/chain_{TEST_PORT}.json'

@pytest.fixture
def blockchain():
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    bc = Blockchain(port=TEST_PORT)
    yield bc
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

def test_integrity_valid_chain(blockchain):
    """Valid chain should pass integrity check."""
    report = blockchain.verify_integrity()
    assert report['valid'] is True
    assert len(report['errors']) == 0
    assert report['blocks_checked'] == 1  # Genesis

def test_integrity_after_mining(blockchain):
    """Chain with mined blocks should pass."""
    proof = blockchain.proof_of_work(blockchain.last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
    
    report = blockchain.verify_integrity()
    assert report['valid'] is True
    assert report['blocks_checked'] == 2

def test_integrity_tampered_hash(blockchain):
    """Detect tampered previous_hash."""
    proof = blockchain.proof_of_work(blockchain.last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
    
    # Tamper with previous_hash
    blockchain.chain[1]['previous_hash'] = 'tampered_hash_value'
    
    report = blockchain.verify_integrity()
    assert report['valid'] is False
    assert any('Invalid previous_hash' in err for err in report['errors'])

def test_integrity_tampered_proof(blockchain):
    """Detect tampered proof of work."""
    proof = blockchain.proof_of_work(blockchain.last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
    
    # Tamper with proof
    blockchain.chain[1]['proof'] = 99999
    
    report = blockchain.verify_integrity()
    assert report['valid'] is False
    assert any('Invalid proof of work' in err for err in report['errors'])
