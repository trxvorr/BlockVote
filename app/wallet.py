import hashlib
import random

import rsa


class Wallet:
    @staticmethod
    def generate_keys():
        """
        Generates a new pair of RSA keys.
        :return: (pub_key_pem, priv_key_pem) as bytes
        """
        (pub_key, priv_key) = rsa.newkeys(2048)
        return pub_key.save_pkcs1(), priv_key.save_pkcs1()

    @staticmethod
    def sign(message, priv_key_pem):
        """
        Sign a message with a private key.
        :param message: <str> Message to sign
        :param priv_key_pem: <bytes> Private key in PEM format
        :return: <bytes> Signature
        """
        priv_key = rsa.PrivateKey.load_pkcs1(priv_key_pem)
        return rsa.sign(message.encode('utf-8'), priv_key, 'SHA-256')

    @staticmethod
    def verify(message, signature, pub_key_pem):
        """
        Verify a signature with a public key.
        :param message: <str> Message
        :param signature: <bytes> Signature
        :param pub_key_pem: <bytes> Public key in PEM format
        :return: <bool> True if valid, False otherwise
        """
        pub_key = rsa.PublicKey.load_pkcs1(pub_key_pem)
        try:
            rsa.verify(message.encode('utf-8'), signature, pub_key)
            return True
        except rsa.VerificationError:
            return False

    @staticmethod
    def load_private_key(priv_key_pem_str):
        """
        Load private key from PEM string or bytes.
        :param priv_key_pem_str: <str> or <bytes>
        :return: <rsa.PrivateKey>
        """
        if isinstance(priv_key_pem_str, str):
            priv_key_pem_str = priv_key_pem_str.encode('utf-8')
        return rsa.PrivateKey.load_pkcs1(priv_key_pem_str)

    @staticmethod
    def get_public_key_pem(priv_key):
        """
        Extract public key PEM from PrivateKey object.
        :param priv_key: <rsa.PrivateKey>
        :return: <bytes> Public Key PEM
        """
        return rsa.PublicKey(priv_key.n, priv_key.e).save_pkcs1()

    # --- Blind Signature Primitives ---
    
    @staticmethod
    def _int_to_bytes(i):
        return i.to_bytes((i.bit_length() + 7) // 8, byteorder='big')

    @staticmethod
    def _bytes_to_int(b):
        return int.from_bytes(b, byteorder='big')

    @staticmethod
    def blind_message(message, pub_key_pem):
        """
        Blind a message so it can be signed without the signer knowing the content.
        m' = m * r^e (mod n)
        :param message: <str> Message to blind
        :param pub_key_pem: <bytes> Signer's public key
        :return: (blinded_msg_int, factor_int)
        """
        pub_key = rsa.PublicKey.load_pkcs1(pub_key_pem)
        
        # Hash the message first to ensure it fits in the modulus
        msg_hash = hashlib.sha256(message.encode('utf-8')).digest()
        m = Wallet._bytes_to_int(msg_hash)
        
        n = pub_key.n
        e = pub_key.e
        
        # Generate random blinding factor r, such that gcd(r, n) = 1
        while True:
            r = random.SystemRandom().randint(1, n - 1)
            # Check if coprime (gcd should be 1)
            # For large primes n=pq, random r is almost certainly coprime.
            # But standard RSA logic checks this.
            # rsa.prime.gcd is not exposed, use math.gcd if needed or just assume likelihood.
            # Ideally we check gcd(r, n) == 1.
            import math
            if math.gcd(r, n) == 1:
                break
                
        # blinded_msg = (m * (r ** e)) % n
        blinded_msg = (m * pow(r, e, n)) % n
        
        return blinded_msg, r

    @staticmethod
    def sign_blind(blinded_msg_int, priv_key_pem):
        """
        Sign a blinded message.
        s' = (m')^d (mod n)
        :param blinded_msg_int: <int> Blinded message
        :param priv_key_pem: <bytes> Signer's private key
        :return: <int> Blind signature
        """
        priv_key = rsa.PrivateKey.load_pkcs1(priv_key_pem)
        n = priv_key.n
        d = priv_key.d
        
        # s' = (m')^d % n
        blind_sig = pow(blinded_msg_int, d, n)
        return blind_sig

    @staticmethod
    def unblind_signature(blind_sig_int, factor_int, pub_key_pem):
        """
        Unblind the signature to get the valid signature for the original message.
        s = s' * r^(-1) (mod n)
        :param blind_sig_int: <int> Blind signature
        :param factor_int: <int> Blinding factor (r)
        :param pub_key_pem: <bytes> Signer's public key
        :return: <int> Unblinded signature (s)
        """
        pub_key = rsa.PublicKey.load_pkcs1(pub_key_pem)
        n = pub_key.n
        
        # Calculate modular inverse of r mod n
        # r^(-1) mod n
        r_inv = pow(factor_int, -1, n)
        
        # s = (s' * r_inv) % n
        signature = (blind_sig_int * r_inv) % n
        return signature

    @staticmethod
    def verify_blind_signature(message, signature_int, pub_key_pem):
        """
        Verify the unblinded signature against the original message.
        s^e = H(m) (mod n)
        :param message: <str> Original message
        :param signature_int: <int> Unblinded signature
        :param pub_key_pem: <bytes> Signer's public key
        :return: <bool> Valid or not
        """
        pub_key = rsa.PublicKey.load_pkcs1(pub_key_pem)
        n = pub_key.n
        e = pub_key.e
        
        msg_hash = hashlib.sha256(message.encode('utf-8')).digest()
        m = Wallet._bytes_to_int(msg_hash)
        
        # Check: s^e % n == m
        signed_val = pow(signature_int, e, n)
        
        return signed_val == m
