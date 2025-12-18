import pytest
import os
from app.blockchain import Blockchain

TEST_PORT = 9994
DATA_DIR = 'data'
FILE_PATH = f'{DATA_DIR}/chain_{TEST_PORT}.json'

@pytest.fixture(autouse=True)
def cleanup():
    # Cleanup before each test
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    yield
    # Cleanup after each test
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)


def test_blockchain_initialization():
    """Test 1: Check if chain has length 1 after initialization (Genesis block)."""
    blockchain = Blockchain(port=TEST_PORT)
    assert len(blockchain.chain) == 1
    assert blockchain.chain[0]['previous_hash'] == '1'
    assert blockchain.chain[0]['proof'] == 100

def test_add_block():
    """Test 2: Check if adding a block increases chain length to 2."""
    blockchain = Blockchain(port=TEST_PORT)
    blockchain.new_block(proof=12345)
    assert len(blockchain.chain) == 2
    assert blockchain.chain[1]['proof'] == 12345
    assert blockchain.chain[1]['index'] == 2

def test_hashing():
    """Test 3: Check if the SHA-256 hash function returns a valid 64-character string."""
    blockchain = Blockchain(port=TEST_PORT)
    block = blockchain.chain[0]
    block_hash = blockchain.hash(block)
    assert isinstance(block_hash, str)
    assert len(block_hash) == 64
