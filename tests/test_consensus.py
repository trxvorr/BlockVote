import os
from unittest.mock import MagicMock, patch

import pytest

from app.blockchain import Blockchain

TEST_PORT = 9992
DATA_DIR = 'data'
FILE_PATH = f'{DATA_DIR}/chain_{TEST_PORT}.json'
FILE_PATH_OTHER = f'{DATA_DIR}/chain_9993.json'

@pytest.fixture
def blockchain():
    # Cleanup before
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    if os.path.exists(FILE_PATH_OTHER):
        os.remove(FILE_PATH_OTHER)
        
    bc = Blockchain(port=TEST_PORT)
    yield bc
    
    # Cleanup after
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    if os.path.exists(FILE_PATH_OTHER):
        os.remove(FILE_PATH_OTHER)

def test_valid_chain(blockchain):
    # Genesis block should be valid
    assert blockchain.valid_chain(blockchain.chain) is True

    # Add a block and check validity
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    assert blockchain.valid_chain(blockchain.chain) is True

def test_invalid_chain(blockchain):
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    # Tamper with the chain
    blockchain.chain[1]['proof'] = 12345  # Invalid proof
    
    assert blockchain.valid_chain(blockchain.chain) is False

def test_resolve_conflicts_authoritative(blockchain):
    # No neighbors, or short/invalid neighbors
    blockchain.nodes.add("node2")
    
    with patch('requests.get') as mock_get:
        # Simulate node2 having a shorter chain
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'length': 1,
            'chain': [blockchain.chain[0]]
        }
        mock_get.return_value = mock_response
        
        replaced = blockchain.resolve_conflicts()
        assert replaced is False

def test_resolve_conflicts_replaced(blockchain):
    blockchain.nodes.add("node2")
    
    # Create a longer valid chain separately with unique port
    other_bc = Blockchain(port=9993)
    proof = other_bc.proof_of_work(other_bc.last_block['proof'])
    other_bc.new_block(proof, other_bc.hash(other_bc.last_block))
    
    # Currently blockchain has length 1, other_bc has length 2
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'length': len(other_bc.chain),
            'chain': other_bc.chain
        }
        mock_get.return_value = mock_response
        
        replaced = blockchain.resolve_conflicts()
        assert replaced is True
        assert len(blockchain.chain) == 2
