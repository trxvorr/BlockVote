import os

import pytest

from app.blockchain import Blockchain

TEST_PORT = 9995
DATA_DIR = 'data'
FILE_PATH = f'{DATA_DIR}/chain_{TEST_PORT}.json'

@pytest.fixture(autouse=True)
def cleanup():
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    yield
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)

def test_register_node():
    blockchain = Blockchain(port=TEST_PORT)
    
    blockchain.register_node('http://192.168.0.5:5000')
    assert '192.168.0.5:5000' in blockchain.nodes

    blockchain.register_node('192.168.0.6:5000')
    assert '192.168.0.6:5000' in blockchain.nodes

def test_register_duplicate_node():
    blockchain = Blockchain(port=TEST_PORT)
    
    blockchain.register_node('http://192.168.0.5:5000')
    blockchain.register_node('http://192.168.0.5:5000')
    
    assert len(blockchain.nodes) == 1

def test_register_invalid_node():
    blockchain = Blockchain(port=TEST_PORT)
    
    # urlparse without scheme often puts everything in path, which our code handles.
    # empty string or something purely invalid usage might raise ValueError or be handled.
    # Our code raises ValueError if both netloc and path are empty.
    
    with pytest.raises(ValueError):
        blockchain.register_node('')
