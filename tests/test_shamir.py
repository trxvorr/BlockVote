from app.shamir import Shamir

def test_shamir_simple_string():
    secret = b"Hello World"
    n = 5
    k = 3
    
    shares = Shamir.split_secret(secret, k, n)
    assert len(shares) == n
    
    # Recover with k shares
    recovered = Shamir.recover_secret(shares[:k])
    assert recovered == secret

def test_shamir_rsa_key():
    # Simulate a larger secret (RSA Key like)
    secret = b"-----BEGIN RSA PRIVATE KEY-----\nMIIEpQIBAAKCAQEA..." * 10
    n = 5
    k = 3
    
    shares = Shamir.split_secret(secret, k, n)
    
    recovered = Shamir.recover_secret(shares[:k])
    assert recovered == secret

def test_shamir_insufficient_shares():
    secret = b"Secret Data"
    n = 5
    k = 3
    shares = Shamir.split_secret(secret, k, n)
    
    # Try with k-1 shares
    recovered = Shamir.recover_secret(shares[:k-1])
    assert recovered != secret

def test_shamir_different_subsets():
    secret = b"Secret Data"
    n = 5
    k = 3
    shares = Shamir.split_secret(secret, k, n)
    
    # Subset [0, 1, 2]
    rec1 = Shamir.recover_secret([shares[0], shares[1], shares[2]])
    assert rec1 == secret

    # Subset [1, 3, 4]
    rec2 = Shamir.recover_secret([shares[1], shares[3], shares[4]])
    assert rec2 == secret
