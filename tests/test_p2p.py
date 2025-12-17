import pytest
from app.blockchain import Blockchain

def test_register_node():
    blockchain = Blockchain()
    
    blockchain.register_node('http://192.168.0.5:5000')
    assert '192.168.0.5:5000' in blockchain.nodes

    blockchain.register_node('192.168.0.6:5000')
    assert '192.168.0.6:5000' in blockchain.nodes

def test_register_duplicate_node():
    blockchain = Blockchain()
    
    blockchain.register_node('http://192.168.0.5:5000')
    blockchain.register_node('http://192.168.0.5:5000')
    
    assert len(blockchain.nodes) == 1

def test_register_invalid_node():
    blockchain = Blockchain()
    
    # urlparse without scheme often puts everything in path, which our code handles.
    # empty string or something purely invalid usage might raise ValueError or be handled.
    # Our code raises ValueError if both netloc and path are empty.
    
    with pytest.raises(ValueError):
        blockchain.register_node('')
