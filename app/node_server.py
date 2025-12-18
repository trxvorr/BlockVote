from sys import argv
from flask import Flask, jsonify, request, render_template
import threading
import socket
import time
import requests
from uuid import uuid4
import json
from textwrap import dedent

from .blockchain import Blockchain
from .wallet import Wallet

# Initialize the Flask App
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Initialize the Blockchain
blockchain = Blockchain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    # Not checking 'signature' and 'public_key' here explicitly for all cases (mining reward?), 
    # but blockchain.new_transaction will enforce it.
    if not all(k in values for k in required):
        return 'Missing values', 400

    try:
        # Signature and Public Key are expected as hex/string in JSON
        # We need to convert them to bytes for the blockchain method if they are hex strings?
        # blockchain.new_transaction expects bytes for sig and pem bytes for key.
        # JSON standardly passes these as strings (hex for sig, string for PEM).
        
        signature = values.get('signature')
        public_key = values.get('public_key')
        
        if signature:
            signature = bytes.fromhex(signature)
        
        if public_key:
             # Ensure it's bytes
             if isinstance(public_key, str):
                 public_key = public_key.encode('utf-8')

        election_id = values.get('election_id', 'default')

        # Create a new Transaction
        index, is_new = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], signature, public_key, election_id)
        
        if is_new:
            # Broadcast to peers
            # We do this asynchronously to avoid blocking
            def broadcast_tx(tx_data):
                for node in blockchain.nodes:
                    try:
                        node_url = f'http://{node}' if '://' not in node else node
                        # POST to peer's /transactions/new
                        # We send the raw values we received
                        requests.post(f'{node_url}/transactions/new', json=tx_data, timeout=2)
                    except:
                        pass
            
            # Start broadcast thread
            threading.Thread(target=broadcast_tx, args=(values,)).start()

        if is_new:
            message = f'Transaction will be added to Block {index}'
            status_code = 201
        else:
            message = f'Transaction already exists in Block {index}'
            status_code = 200

        response = {'message': message}
        return jsonify(response), status_code
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500

@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes', methods=['GET'])
def get_nodes():
    return jsonify({'nodes': list(blockchain.nodes)}), 200

@app.route('/votes/count', methods=['GET'])
def count_votes():
    results = blockchain.count_votes()
    return jsonify(results), 200

@app.route('/election/window', methods=['POST'])
def set_election_window():
    values = request.get_json()
    start_time = values.get('start_time')
    end_time = values.get('end_time')
    
    if start_time is None or end_time is None:
        return 'Missing start_time or end_time', 400
    
    blockchain.set_election_window(start_time, end_time)
    
    return jsonify({'message': 'Election window configured'}), 200

# UDP port for broadcasting presence
BROADCAST_PORT = 54321
peer_discovery_active = True

def broadcast_presence(my_port):
    """
    Broadcast presence to the LAN so other nodes can find us.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f"BLOCKVOTE_HELLO {my_port}".encode('utf-8')
        while peer_discovery_active:
            try:
                s.sendto(message, ('<broadcast>', BROADCAST_PORT))
                time.sleep(5)  # Broadcast every 5 seconds
            except Exception as e:
                print(f"Error broadcasting: {e}")
                time.sleep(5)

def listen_for_peers(my_port):
    """
    Listen for other nodes broadcasting their presence.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', BROADCAST_PORT))
        while peer_discovery_active:
            try:
                data, addr = s.recvfrom(1024)
                message = data.decode('utf-8')
                if message.startswith("BLOCKVOTE_HELLO"):
                    peer_port = int(message.split()[1])
                    peer_ip = addr[0]
                    
                    # Don't register ourselves
                    # We can't easily check if peer_ip is us if we listen on 0.0.0.0, 
                    # but if the port matches our port, it's likely us (on verify same machine).
                    # A better check is needed for production, but this suffices for simple local/LAN.
                    if peer_port != my_port:
                        peer_address = f"http://{peer_ip}:{peer_port}"
                        if f"{peer_ip}:{peer_port}" not in blockchain.nodes:
                            print(f"Discovered peer: {peer_address}")
                            blockchain.register_node(peer_address)
                            # Optionally: Tell them about us immediately via HTTP
                            # requests.post(f"{peer_address}/nodes/register", json={'nodes': [f"http://{my_ip}:{my_port}"]})
            except Exception as e:
                print(f"Error listening for peers: {e}")


# In-memory candidate registry (for demo purposes)
CANDIDATES = set()

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/candidates', methods=['GET'])
def get_candidates():
    return jsonify({'candidates': list(CANDIDATES)}), 200

@app.route('/candidates/add', methods=['POST'])
def add_candidate():
    values = request.get_json()
    if not values or 'name' not in values:
        return 'Missing name', 400
    
    CANDIDATES.add(values['name'])
    return jsonify({'message': f"Candidate {values['name']} added"}), 201

@app.route('/stats', methods=['GET'])
def get_stats():
    response = {
        'chain_length': len(blockchain.chain),
        'nodes_count': len(blockchain.nodes),
        'last_block_index': blockchain.last_block['index'],
        'node_id': node_identifier
    }
    return jsonify(response), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote/submit', methods=['POST'])
def submit_vote():
    values = request.get_json()
    
    required = ['candidate', 'private_key']
    if not all(k in values for k in required):
        return jsonify({'message': 'Missing values'}), 400

    candidate = values['candidate']
    priv_key_pem = values['private_key']
    election_id = values.get('election_id', 'default')

    try:
        # 1. Load keys
        priv_key = Wallet.load_private_key(priv_key_pem)
        pub_key_pem = Wallet.get_public_key_pem(priv_key)
        
        # 2. Derive Sender Address (Use PubKey hash or just PubKey PEM for now)
        # Using PubKey PEM as sender ID for simplicity in this demo
        sender = pub_key_pem.decode('utf-8')
        
        # 3. Create Transaction Data
        transaction_data = {
            'sender': sender,
            'recipient': candidate,
            'amount': 1,
            'election_id': election_id
        }
        
        # 4. Sign
        message = json.dumps(transaction_data, sort_keys=True)
        signature = Wallet.sign(message, priv_key).hex()
        
        # 5. Submit to Blockchain
        # Note: We are doing a local call, bypassing the request.post usually done by clients.
        # But we need to use the endpoint or direct method? 
        # Direct method allows us to check return values easily, but endpoint logic has broadcast.
        # Let's call direct method and then handle broadcast manually or via internal logic.
        # Actually, let's just reuse the /transactions/new logic or call it internally?
        # Re-implementing logic here is safer for "Hosted Wallet" specific handling.
        
        index, is_new = blockchain.new_transaction(sender, candidate, 1, bytes.fromhex(signature), pub_key_pem, election_id)
        
        if is_new:
             # Broadcast (Simple version)
             def broadcast_tx(tx_data):
                for node in blockchain.nodes:
                    try:
                        node_url = f'http://{node}' if '://' not in node else node
                        requests.post(f'{node_url}/transactions/new', json=tx_data, timeout=2)
                    except:
                        pass
             
             payload = {
                 'sender': sender,
                 'recipient': candidate,
                 'amount': 1,
                 'signature': signature,
                 'public_key': sender, # sent as PEM string
                 'election_id': election_id
             }
             threading.Thread(target=broadcast_tx, args=(payload,)).start()

        return jsonify({'message': f'Vote submitted successfully! Block Index: {index}'}), 201

    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    # If the user provides a port number, use it. Otherwise, default to 5000.
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 5000
    
    # Re-initialize blockchain with correct port for persistence file
    # Note: We initialized 'blockchain' globally at the top. 
    # Python globals can be modified if we are careful, or we just rely on default.
    # To properly support persistence per port, we need to re-init here or change the global init structure.
    # Changing the global variable 'blockchain' here works for the Flask app within this process.
    blockchain.__init__(port)

    # Start P2P Discovery Threads
    t1 = threading.Thread(target=broadcast_presence, args=(port,), daemon=True)
    t2 = threading.Thread(target=listen_for_peers, args=(port,), daemon=True)
    t1.start()
    t2.start()
        
    app.run(host='0.0.0.0', port=port)
