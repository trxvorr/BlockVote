from flask import Flask, jsonify, request

from .wallet import Wallet

# Initialize the Flask App
app = Flask(__name__)

# Admin Storage
admin_pub_key = None
admin_priv_key = None
voters_who_signed = set()

def initialize_keys():
    global admin_pub_key, admin_priv_key
    # In a real app, load from secure storage. Here, generate fresh on start.
    print("Generating Admin Keys...")
    admin_pub_key, admin_priv_key = Wallet.generate_keys()
    print("Admin Keys Generated.")

@app.route('/', methods=['GET'])
def home():
    return "BlockVote Admin Authority is Running", 200

@app.route('/admin/key', methods=['GET'])
def get_key():
    if not admin_pub_key:
        return "Keys not initialized", 500
    
    return jsonify({
        'public_key': admin_pub_key.decode('utf-8')
    }), 200

@app.route('/admin/sign', methods=['POST'])
def sign_blindly():
    values = request.get_json()
    
    required = ['voter_id', 'blinded_hash']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    voter_id = values['voter_id']
    blinded_hash = values['blinded_hash']
    
    # 1. Check Eligibility (Mock: All are eligible)
    # 2. Check Double Voting
    if voter_id in voters_who_signed:
        return jsonify({'message': 'Voter has already obtained a signature'}), 403
    
    # 3. Sign Blindly
    try:
        # Expecting integer for blinded_hash
        blinded_hash_int = int(blinded_hash)
        signature = Wallet.sign_blind(blinded_hash_int, admin_priv_key)
        
        voters_who_signed.add(voter_id)
        
        return jsonify({
            'blind_signature': signature
        }), 201
    except ValueError:
        return "Invalid blinded hash format", 400
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    initialize_keys()
    app.run(host='0.0.0.0', port=5001)
