import os
import hashlib
import json
import time
import requests
from urllib.parse import urlparse
from .wallet import Wallet


class Blockchain:
    def __init__(self, port=5000):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.data_dir = 'data'
        self.file_path = f'{self.data_dir}/chain_{port}.json'
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Attempt to load state
        if not self.load_state():
            # Create the genesis block if no saved state
            self.new_block(previous_hash='1', proof=100)
    
    def load_state(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    self.chain = data.get('chain', [])
                    self.current_transactions = data.get('transactions', [])
                    self.nodes = set(data.get('nodes', []))
                    return True
            except Exception as e:
                print(f"Error loading state: {e}")
                return False
        return False

    def save_state(self):
        data = {
            'chain': self.chain,
            'transactions': self.current_transactions,
            'nodes': list(self.nodes)
        }
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving state: {e}")

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)

        self.save_state()
        return block

    def new_transaction(self, sender, recipient, amount, signature=None, public_key=None):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :param signature: <bytes> (Optional) SHA-256 signature
        :param public_key: <bytes> (Optional) Public key to verify signature
        :return: <int> The index of the Block that will hold this transaction
        """
        
        # Verify Signature (skip for mining rewards usually designated by sender='0')
        if sender != '0':
            if not signature or not public_key:
                raise ValueError("Transaction signature and public key are required.")
            
            # Reconstruct the message that was signed. 
            # Ideally this matches exactly what the client signed.
            # Simple format: sender+recipient+str(amount) or json? 
            # Let's use ordered json string of data to be safe and consistent.
            transaction_data = {
                'sender': sender,
                'recipient': recipient,
                'amount': amount
            }
            # Message is the string representation
            message = json.dumps(transaction_data, sort_keys=True)
            
            # Since signature and public_key come in likely as hex or string from API, 
            # we might need to handle conversion. But internally Python usually deals with bytes for crypto.
            # Let's assume they are passed as appropriate types (bytes) or handle conversion if strings.
            # If coming from our API, they might be hex strings or PEM strings.
            # Wallet.verify expects bytes for signature and PEM bytes for key.
            
            # However, new_transaction is internal logic. The API layer (node_server) should handle parsing?
            # Or we handle it here.
            # Let's assume they are passed as is from the caller. 
            
            if not Wallet.verify(message, signature, public_key):
                 raise ValueError("Invalid Transaction Signature")

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            # We don't necessarily need to store the signature in the chain for this simple demo,
            # but usually you DO store it to prove validity later.
            'signature': signature.hex() if isinstance(signature, bytes) else signature,
            # public_key? Maybe too large to store every time if it's PEM. 
            # But "sender" is often the Hash of PubKey.
            # For this demo, let's keep it simple.
        })
        
        self.save_state()

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')
            
        self.save_state()

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # print(f'{last_block}')
            # print(f'{block}')
            # print("\n-----------\n")
            
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            try:
                # We assume protocol is http for now, usually stored in node list
                # But previously we stored netloc. We need to handle scheme.
                # Let's assume http if missing or we stored full URL previously?
                # In register_node we stored netloc or path.
                # Best to ensure we construct a valid URL.
                if '://' not in node:
                     node_url = f'http://{node}'
                else:
                     node_url = node
                     
                response = requests.get(f'{node_url}/chain')

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    # Check if the length is longer and the chain is valid
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            except requests.exceptions.RequestException:
                # Node is unreachable, ignore.
                continue

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            self.save_state()
            return True

        return False
