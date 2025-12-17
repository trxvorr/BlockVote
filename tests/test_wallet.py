from app.wallet import Wallet

def test_generate_keys():
    pub_key, priv_key = Wallet.generate_keys()
    assert pub_key is not None
    assert priv_key is not None
    assert b'BEGIN RSA PUBLIC KEY' in pub_key
    assert b'BEGIN RSA PRIVATE KEY' in priv_key

def test_sign_and_verify():
    pub_key, priv_key = Wallet.generate_keys()
    message = "Hello, BlockVote!"
    
    signature = Wallet.sign(message, priv_key)
    assert signature is not None
    
    is_valid = Wallet.verify(message, signature, pub_key)
    assert is_valid is True

def test_verify_invalid_signature():
    pub_key, priv_key = Wallet.generate_keys()
    message = "Hello, BlockVote!"
    signature = Wallet.sign(message, priv_key)
    
    # Tamper with signature
    tampered_sig = bytearray(signature)
    tampered_sig[0] = tampered_sig[0] ^ 0xFF
    
    is_valid = Wallet.verify(message, bytes(tampered_sig), pub_key)
    assert is_valid is False

def test_blind_signature_flow():
    # 1. Setup: Admin Authority (Signer) has keys
    admin_pub, admin_priv = Wallet.generate_keys()
    
    # 2. Voter: Prepares a vote (message) and blinds it
    vote_message = "Vote for Alice"
    blinded_msg, r = Wallet.blind_message(vote_message, admin_pub)
    
    assert blinded_msg is not None
    assert r is not None
    
    # 3. Admin: Signs the blinded message (without seeing "Vote for Alice")
    blind_sig = Wallet.sign_blind(blinded_msg, admin_priv)
    
    # 4. Voter: Unblinds the signature to get valid signature for original vote
    signature_int = Wallet.unblind_signature(blind_sig, r, admin_pub)
    
    # 5. Anyone: Verifies the unblinded signature matches the original vote
    is_valid = Wallet.verify_blind_signature(vote_message, signature_int, admin_pub)
    
    assert is_valid is True

def test_blind_signature_tamper():
    admin_pub, admin_priv = Wallet.generate_keys()
    vote_message = "Vote for Alice"
    blinded_msg, r = Wallet.blind_message(vote_message, admin_pub)
    blind_sig = Wallet.sign_blind(blinded_msg, admin_priv)
    signature_int = Wallet.unblind_signature(blind_sig, r, admin_pub)
    
    # Verify against WRONG message
    is_valid = Wallet.verify_blind_signature("Vote for Bob", signature_int, admin_pub)
    assert is_valid is False
