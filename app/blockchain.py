import hashlib
import json
import time
from urllib.parse import urlparse
from .wallet import Wallet


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)
        
        self.nodes = set()

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

        return self.last_block['index'] + 1

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
