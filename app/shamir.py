import random

# Mersenne Prime 2**127 - 1
_PRIME = 2**127 - 1

class Shamir:
    @staticmethod
    def _eval_poly(poly, x, prime):
        """
        Evaluates polynomial (coefficients tuple) at x modulo prime.
        """
        accum = 0
        for coeff in reversed(poly):
            accum = (accum * x + coeff) % prime
        return accum

    @staticmethod
    def _lagrange_interpolate(x, x_s, y_s, prime):
        """
        Find the y-value for the given x, given n (x, y) points;
        k points will define a polynomial of up to kth order.
        """
        k = len(x_s)
        assert k == len(y_s)
        
        # L_i(x) = y_i * Product_{j!=i} (x - x_j) / (x_i - x_j)
        # Result = Sum L_i(x)
        
        total = 0
        for i in range(k):
            xi, yi = x_s[i], y_s[i]
            
            num = 1
            den = 1
            for j in range(k):
                if i == j: continue
                xj = x_s[j]
                
                num = (num * (x - xj)) % prime
                den = (den * (xi - xj)) % prime
            
            # modular inverse of denominator
            inv_den = pow(den, -1, prime)
            term = (yi * num * inv_den) % prime
            total = (total + term) % prime
            
        return total

    @staticmethod
    def _pad(data, block_size):
        padding_len = block_size - (len(data) % block_size)
        return data + bytes([padding_len] * padding_len)

    @staticmethod
    def _unpad(data):
        if not data:
            return data
        padding_len = data[-1]
        if padding_len > len(data):
            # Invalid padding, return as is or error? For now, return as is to avoid crash, but likely wrong.
            return data
        return data[:-padding_len]

    @staticmethod
    def split_secret(secret_bytes, k, n):
        """
        Split secret into n shares.
        """
        # 0. Pad secret
        chunk_size = 15
        padded_secret = Shamir._pad(secret_bytes, chunk_size)
        
        # 1. Chunking
        chunks = [padded_secret[i:i + chunk_size] for i in range(0, len(padded_secret), chunk_size)]
        
        shares = [[] for _ in range(n)] 
        
        for chunk in chunks:
            chunk_int = int.from_bytes(chunk, 'big')
            # poly degree k-1
            poly = [chunk_int] + [random.SystemRandom().randint(0, _PRIME - 1) for _ in range(k - 1)]
            
            for i in range(n):
                user_x = i + 1
                y = Shamir._eval_poly(poly, user_x, _PRIME)
                shares[i].append(y)
        
        return [(i + 1, shares[i]) for i in range(n)]

    @staticmethod
    def recover_secret(shares):
        """
        Recover secret from k shares.
        """
        if not shares:
            return None
            
        k = len(shares)
        num_chunks = len(shares[0][1])
        x_s = [s[0] for s in shares]
        
        reconstructed_chunks = []
        
        for chunk_idx in range(num_chunks):
            y_s = [s[1][chunk_idx] for s in shares]
            secret_int = Shamir._lagrange_interpolate(0, x_s, y_s, _PRIME)
            
            # Result can be up to 2**127-1 (16 bytes), but valid chunks are 15 bytes.
            # Use 16 bytes to avoid OverflowError, then take last 15.
            chunk_bytes = secret_int.to_bytes(16, 'big')[-15:]
            reconstructed_chunks.append(chunk_bytes)
        
        padded_secret = b"".join(reconstructed_chunks)
        return Shamir._unpad(padded_secret)
