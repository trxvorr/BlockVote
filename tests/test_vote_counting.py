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

def test_vote_counting_empty(blockchain):
    # Only genesis block, no votes
    results = blockchain.count_votes()
    assert results == {}

def test_vote_counting_basic(blockchain):
    # Add block with votes
    # 1. Candidate A receives 1 vote
    # 2. Candidate B receives 2 votes
    
    pub, priv = Wallet.generate_keys()
    
    # Tx 1: A receives 1
    # Note: explicit 'election_id': 'default' for signing
    blockchain.new_transaction("voter1", "CandidateA", 1, 
                              Wallet.sign(json.dumps({'sender': "voter1", 'recipient': "CandidateA", 'amount': 1, 'election_id': 'default'}, sort_keys=True), priv), pub)
    
    # Tx 2: B receives 1
    blockchain.new_transaction("voter2", "CandidateB", 1,
                              Wallet.sign(json.dumps({'sender': "voter2", 'recipient': "CandidateB", 'amount': 1, 'election_id': 'default'}, sort_keys=True), priv), pub)
    
    # Mine block to confirm transactions
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    # Add another block
    # Tx 3: A receives another 1
    blockchain.new_transaction("voter3", "CandidateA", 1,
                              Wallet.sign(json.dumps({'sender': "voter3", 'recipient': "CandidateA", 'amount': 1, 'election_id': 'default'}, sort_keys=True), priv), pub)
    
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    # Count
    results = blockchain.count_votes()
    
    # Updated structure: {'default': {'CandidateA': 2, 'CandidateB': 1}}
    assert results['default']['CandidateA'] == 2
    assert results['default']['CandidateB'] == 1

def test_vote_counting_excludes_mining_rewards(blockchain):
    # Mine a block (creates reward tx)
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block['proof'])
    
    # Manually add reward to mempool? mining endpoint does it.
    # Let's call new_transaction manually as miner does
    blockchain.new_transaction("0", "miner_id", 1)
    
    blockchain.new_block(proof, blockchain.hash(last_block))
    
    results = blockchain.count_votes()
    assert results == {}  # "miner_id" should NOT be counted as a candidate
