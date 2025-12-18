"""
Stress tests for BlockVote system.
Run with: pytest tests/test_stress.py -v -s
"""
import pytest
import os
import time
import concurrent.futures
from app.blockchain import Blockchain
from app.wallet import Wallet
import json

TEST_PORT = 9997
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

class TestPerformance:
    """Performance benchmark tests."""
    
    def test_mining_performance(self, blockchain):
        """Measure proof of work mining time."""
        times = []
        
        for i in range(3):  # Mine 3 blocks
            start = time.time()
            last_proof = blockchain.last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"Block {i+1} mined in {elapsed:.3f}s")
        
        avg_time = sum(times) / len(times)
        print(f"\nAverage mining time: {avg_time:.3f}s")
        
        # Should mine within reasonable time (depends on difficulty)
        assert avg_time < 30, f"Mining too slow: {avg_time:.3f}s average"
    
    def test_transaction_throughput(self, blockchain):
        """Measure transaction creation throughput."""
        pub, priv = Wallet.generate_keys()
        
        num_transactions = 50
        start = time.time()
        
        for i in range(num_transactions):
            sender = f"voter_{i}"
            recipient = "candidate_a"
            
            transaction_data = {
                'sender': sender,
                'recipient': recipient,
                'amount': 1,
                'election_id': 'stress_test'
            }
            message = json.dumps(transaction_data, sort_keys=True)
            signature = Wallet.sign(message, priv)
            
            blockchain.new_transaction(sender, recipient, 1, signature, pub, 'stress_test')
        
        elapsed = time.time() - start
        tps = num_transactions / elapsed
        
        print(f"\n{num_transactions} transactions in {elapsed:.3f}s")
        print(f"Throughput: {tps:.1f} transactions/second")
        
        assert tps > 10, f"Transaction throughput too low: {tps:.1f} TPS"
    
    def test_chain_verification_performance(self, blockchain):
        """Measure chain verification time."""
        # First, build a chain with some blocks
        for _ in range(5):
            last_proof = blockchain.last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
        
        # Now measure verification
        start = time.time()
        iterations = 100
        
        for _ in range(iterations):
            result = blockchain.verify_integrity()
            assert result['valid'] is True
        
        elapsed = time.time() - start
        per_verification = elapsed / iterations * 1000  # ms
        
        print(f"\n{iterations} verifications in {elapsed:.3f}s")
        print(f"Average: {per_verification:.2f}ms per verification")
        print(f"Blocks checked per verification: {result['blocks_checked']}")
        
        assert per_verification < 100, f"Verification too slow: {per_verification:.2f}ms"
    
    def test_concurrent_operations(self, blockchain):
        """Test concurrent transaction submissions."""
        pub, priv = Wallet.generate_keys()
        
        def create_transaction(i):
            sender = f"concurrent_voter_{i}"
            transaction_data = {
                'sender': sender,
                'recipient': 'candidate_concurrent',
                'amount': 1,
                'election_id': 'concurrent_test'
            }
            message = json.dumps(transaction_data, sort_keys=True)
            signature = Wallet.sign(message, priv)
            return blockchain.new_transaction(sender, 'candidate_concurrent', 1, signature, pub, 'concurrent_test')
        
        num_concurrent = 20
        start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_transaction, i) for i in range(num_concurrent)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed = time.time() - start
        
        print(f"\n{num_concurrent} concurrent transactions in {elapsed:.3f}s")
        print(f"Successful: {len([r for r in results if r[1]])}")
        
        assert len(blockchain.current_transactions) >= num_concurrent * 0.9, "Lost transactions under concurrency"


class TestStressLimits:
    """Test system behavior under stress."""
    
    def test_large_chain_verification(self, blockchain):
        """Test verification with larger chain."""
        # Build a longer chain
        for i in range(10):
            last_proof = blockchain.last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
            if (i + 1) % 5 == 0:
                print(f"Built {i + 1} blocks...")
        
        # Verify
        start = time.time()
        result = blockchain.verify_integrity()
        elapsed = time.time() - start
        
        print(f"\nVerified {result['blocks_checked']} blocks in {elapsed:.3f}s")
        assert result['valid'] is True
        assert elapsed < 1.0, f"Large chain verification too slow: {elapsed:.3f}s"
