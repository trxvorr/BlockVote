import pytest
from app.blockchain import Blockchain

def test_blockchain_initialization():
    """Test 1: Check if chain has length 1 after initialization (Genesis block)."""
    blockchain = Blockchain()
    assert len(blockchain.chain) == 1
    assert blockchain.chain[0]['previous_hash'] == '1'
    assert blockchain.chain[0]['proof'] == 100

def test_add_block():
    """Test 2: Check if adding a block increases chain length to 2."""
    blockchain = Blockchain()
    blockchain.new_block(proof=12345)
    assert len(blockchain.chain) == 2
    assert blockchain.chain[1]['proof'] == 12345
    assert blockchain.chain[1]['index'] == 2

def test_hashing():
    """Test 3: Check if the SHA-256 hash function returns a valid 64-character string."""
    blockchain = Blockchain()
    block = blockchain.chain[0]
    block_hash = blockchain.hash(block)
    assert isinstance(block_hash, str)
    assert len(block_hash) == 64
