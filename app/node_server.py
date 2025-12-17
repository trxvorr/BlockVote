from sys import argv
from flask import Flask, jsonify, request
import threading
import socket
import time
import requests

from .blockchain import Blockchain

# Initialize the Flask App
app = Flask(__name__)

# Initialize the Blockchain
blockchain = Blockchain()

@app.route('/', methods=['GET'])
def home():
    return "BlockVote Node is Running Successfully!", 200

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

        # Create a new Transaction
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], signature, public_key)

        response = {'message': f'Transaction will be added to Block {index}'}
        return jsonify(response), 201
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500

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

if __name__ == '__main__':
    # If the user provides a port number, use it. Otherwise, default to 5000.
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 5000
    
    # Start P2P Discovery Threads
    t1 = threading.Thread(target=broadcast_presence, args=(port,), daemon=True)
    t2 = threading.Thread(target=listen_for_peers, args=(port,), daemon=True)
    t1.start()
    t2.start()
        
    app.run(host='0.0.0.0', port=port)
