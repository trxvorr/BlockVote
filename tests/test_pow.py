import pytest
from app.blockchain import Blockchain

def test_valid_proof_true():
    # Known working pair for "0000" prefix using this algorithm?
    # Calculating one manually or trusting implementation to find one.
    # Blockchain.proof_of_work calls proof_of_work(100) in __init__ for verifying? No.
    # Genesis block: proof=100.
    
    last_proof = 100
    proof = Blockchain().proof_of_work(last_proof)
    assert Blockchain.valid_proof(last_proof, proof) is True

def test_valid_proof_false():
    last_proof = 100
    proof = 1  # Unlikely to be correct
    # Unless 1001 hashes to 0000...
    
    # Just check that a random number returns False usually
    assert Blockchain.valid_proof(last_proof, proof) is False

def test_proof_of_work_solver():
    blockchain = Blockchain()
    last_proof = 100
    proof = blockchain.proof_of_work(last_proof)
    
    # Verify result
    assert isinstance(proof, int)
    assert Blockchain.valid_proof(last_proof, proof) is True
