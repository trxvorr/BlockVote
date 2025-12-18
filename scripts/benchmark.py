#!/usr/bin/env python3
"""
BlockVote Benchmark Script

Run standalone: python scripts/benchmark.py
"""
import json
import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.blockchain import Blockchain
from app.wallet import Wallet


def benchmark_mining(blockchain, num_blocks=5):
    """Benchmark mining performance."""
    print(f"\n{'='*50}")
    print("MINING BENCHMARK")
    print(f"{'='*50}")
    
    times = []
    for i in range(num_blocks):
        start = time.time()
        last_proof = blockchain.last_block['proof']
        proof = blockchain.proof_of_work(last_proof)
        blockchain.new_block(proof, blockchain.hash(blockchain.last_block))
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  Block {i+1}: {elapsed:.3f}s (proof={proof})")
    
    avg = sum(times) / len(times)
    print("\n  Results:")
    print(f"    Blocks mined: {num_blocks}")
    print(f"    Total time: {sum(times):.3f}s")
    print(f"    Average: {avg:.3f}s per block")
    print(f"    Min: {min(times):.3f}s")
    print(f"    Max: {max(times):.3f}s")
    
    return avg

def benchmark_transactions(blockchain, num_tx=100):
    """Benchmark transaction throughput."""
    print(f"\n{'='*50}")
    print("TRANSACTION THROUGHPUT BENCHMARK")
    print(f"{'='*50}")
    
    pub, priv = Wallet.generate_keys()
    
    start = time.time()
    for i in range(num_tx):
        sender = f"bench_voter_{i}"
        transaction_data = {
            'sender': sender,
            'recipient': 'candidate_bench',
            'amount': 1,
            'election_id': 'benchmark'
        }
        message = json.dumps(transaction_data, sort_keys=True)
        signature = Wallet.sign(message, priv)
        blockchain.new_transaction(sender, 'candidate_bench', 1, signature, pub, 'benchmark')
    
    elapsed = time.time() - start
    tps = num_tx / elapsed
    
    print("\n  Results:")
    print(f"    Transactions: {num_tx}")
    print(f"    Total time: {elapsed:.3f}s")
    print(f"    Throughput: {tps:.1f} TPS")
    print(f"    Avg per tx: {(elapsed/num_tx)*1000:.2f}ms")
    
    return tps

def benchmark_verification(blockchain):
    """Benchmark chain verification."""
    print(f"\n{'='*50}")
    print("CHAIN VERIFICATION BENCHMARK")
    print(f"{'='*50}")
    
    iterations = 1000
    start = time.time()
    
    for _ in range(iterations):
        blockchain.verify_integrity()
    
    elapsed = time.time() - start
    per_check = (elapsed / iterations) * 1000
    
    print("\n  Results:")
    print(f"    Chain length: {len(blockchain.chain)} blocks")
    print(f"    Iterations: {iterations}")
    print(f"    Total time: {elapsed:.3f}s")
    print(f"    Avg per check: {per_check:.3f}ms")
    print(f"    Checks/second: {iterations/elapsed:.1f}")
    
    return per_check

def main():
    print("\n" + "="*60)
    print("     BLOCKVOTE PERFORMANCE BENCHMARK")
    print("="*60)
    
    # Create fresh blockchain
    test_port = 9998
    data_file = f'data/chain_{test_port}.json'
    
    if os.path.exists(data_file):
        os.remove(data_file)
    
    blockchain = Blockchain(port=test_port)
    
    # Run benchmarks
    mining_avg = benchmark_mining(blockchain, num_blocks=3)
    tps = benchmark_transactions(blockchain, num_tx=100)
    verify_ms = benchmark_verification(blockchain)
    
    # Summary
    print(f"\n{'='*60}")
    print("     SUMMARY")
    print(f"{'='*60}")
    print(f"  Mining:        {mining_avg:.3f}s avg per block")
    print(f"  Transactions:  {tps:.1f} TPS")
    print(f"  Verification:  {verify_ms:.3f}ms per check")
    print("\n  Chain stats:")
    print(f"    Total blocks: {len(blockchain.chain)}")
    print(f"    Pending tx:   {len(blockchain.current_transactions)}")
    print("="*60 + "\n")
    
    # Cleanup
    if os.path.exists(data_file):
        os.remove(data_file)

if __name__ == '__main__':
    main()
