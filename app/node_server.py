from sys import argv
from flask import Flask, jsonify, request, render_template, redirect, url_for
import threading
import socket
import time
import requests
import random
import os
from datetime import datetime
from uuid import uuid4
import json
from textwrap import dedent

from .blockchain import Blockchain
from .wallet import Wallet

# Initialize the Flask App
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'blockvote-secret-key')

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Initialize the Blockchain
blockchain = Blockchain()

# OTP Authentication Store
OTP_STORE = {}  # {email: {'otp': str, 'expires': float}}
VERIFIED_SESSIONS = set()  # Set of valid session tokens

# Admin Authentication
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
ADMIN_SESSIONS = set()  # Set of valid admin session tokens

# Activity Log (ring buffer)
ACTIVITY_LOG = []
MAX_LOG_ENTRIES = 100

def log_activity(level, message):
    """Log an activity entry."""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'level': level,
        'message': message
    }
    ACTIVITY_LOG.append(entry)
    if len(ACTIVITY_LOG) > MAX_LOG_ENTRIES:
        ACTIVITY_LOG.pop(0)
    # Also print to console
    print(f"[{entry['timestamp']}] [{level}] {message}")

def require_admin(f):
    """Decorator to require admin authentication."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('admin_session') or request.headers.get('X-Admin-Token')
        if not token or token not in ADMIN_SESSIONS:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'message': 'Admin authentication required'}), 401
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated


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
    log_activity('INFO', f"Block {block['index']} mined with {len(block['transactions'])} transactions")
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

# --- Admin Authentication Routes ---
@app.route('/admin/login', methods=['GET'])
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    values = request.get_json()
    password = values.get('password') if values else None
    
    if password == ADMIN_PASSWORD:
        token = str(uuid4())
        ADMIN_SESSIONS.add(token)
        log_activity('INFO', 'Admin login successful')
        response = jsonify({'message': 'Login successful', 'token': token})
        response.set_cookie('admin_session', token, httponly=True, samesite='Lax')
        return response, 200
    else:
        log_activity('WARNING', 'Admin login failed - incorrect password')
        return jsonify({'message': 'Invalid password'}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    token = request.cookies.get('admin_session')
    if token and token in ADMIN_SESSIONS:
        ADMIN_SESSIONS.discard(token)
    log_activity('INFO', 'Admin logged out')
    response = jsonify({'message': 'Logged out'})
    response.delete_cookie('admin_session')
    return response, 200

@app.route('/admin')
@require_admin
def admin():
    return render_template('admin.html')

@app.route('/logs/recent', methods=['GET'])
@require_admin
def get_logs():
    return jsonify({'logs': ACTIVITY_LOG[-50:]}), 200

@app.route('/candidates', methods=['GET'])
def get_candidates():
    return jsonify({'candidates': list(CANDIDATES)}), 200

@app.route('/candidates/add', methods=['POST'])
@require_admin
def add_candidate():
    values = request.get_json()
    if not values or 'name' not in values:
        return 'Missing name', 400
    
    CANDIDATES.add(values['name'])
    log_activity('INFO', f"Candidate '{values['name']}' added")
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

@app.route('/chain/verify', methods=['GET'])
def verify_chain():
    """Verify blockchain integrity and return detailed report."""
    report = blockchain.verify_integrity()
    status_code = 200 if report['valid'] else 409  # 409 Conflict if invalid
    return jsonify(report), status_code

# --- OTP Authentication ---
@app.route('/auth/request-otp', methods=['POST'])
def request_otp():
    values = request.get_json()
    email = values.get('email')
    
    if not email:
        return jsonify({'message': 'Email is required'}), 400
    
    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))
    expires = time.time() + 300  # 5 minutes
    
    OTP_STORE[email] = {'otp': otp, 'expires': expires}
    
    # Simulate email by logging to console
    print(f"\n{'='*50}")
    print(f"[OTP] Email: {email}")
    print(f"[OTP] Code: {otp}")
    print(f"[OTP] Expires in 5 minutes")
    print(f"{'='*50}\n")
    
    return jsonify({'message': 'OTP sent to your email (check console)'}), 200

@app.route('/auth/verify-otp', methods=['POST'])
def verify_otp():
    values = request.get_json()
    email = values.get('email')
    otp = values.get('otp')
    
    if not email or not otp:
        return jsonify({'message': 'Email and OTP are required'}), 400
    
    stored = OTP_STORE.get(email)
    
    if not stored:
        return jsonify({'message': 'No OTP requested for this email'}), 400
    
    if time.time() > stored['expires']:
        del OTP_STORE[email]
        return jsonify({'message': 'OTP has expired'}), 400
    
    if stored['otp'] != otp:
        return jsonify({'message': 'Invalid OTP'}), 400
    
    # OTP valid - create session
    session_token = str(uuid4())
    VERIFIED_SESSIONS.add(session_token)
    del OTP_STORE[email]
    
    return jsonify({'message': 'Verification successful', 'session_token': session_token}), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vote/submit', methods=['POST'])
def submit_vote():
    values = request.get_json()
    
    # Validate session token (OTP verification)
    session_token = values.get('session_token')
    if not session_token or session_token not in VERIFIED_SESSIONS:
        return jsonify({'message': 'Please verify your email first'}), 401
    
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

        log_activity('INFO', f"Vote submitted for '{candidate}' in election '{election_id}'")
        return jsonify({'message': f'Vote submitted successfully! Block Index: {index}'}), 201

    except ValueError as e:
        log_activity('WARNING', f"Vote failed: {str(e)}")
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        log_activity('ERROR', f"Vote error: {str(e)}")
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
