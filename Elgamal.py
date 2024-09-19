import random

# Custom function to compute the modular inverse using the Extended Euclidean Algorithm
def mod_inverse(a, p):
    """
    Compute the modular inverse of a modulo p using the Extended Euclidean Algorithm.
    Returns the modular inverse of a mod p.
    """
    t, new_t = 0, 1
    r, new_r = p, a

    while new_r != 0:
        quotient = r // new_r
        t, new_t = new_t, t - quotient * new_t
        r, new_r = new_r, r - quotient * new_r

    if r > 1:
        raise ValueError(f"{a} does not have an inverse modulo {p}")
    if t < 0:
        t = t + p

    return t

# Function to generate a large prime number of specified bit length
def find_large_prime(bit_length=32):
    def is_prime(n):
        if n <= 1:
            return False
        if n <= 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    while True:
        p_candidate = random.getrandbits(bit_length)
        p_candidate |= (1 << (bit_length - 1)) | 1  # Ensure it is odd and correct bit length
        if is_prime(p_candidate):
            return p_candidate

# Function to find a generator for the prime number p
def find_generator(p):
    for g in range(2, p):
        if pow(g, 2, p) != 1 and pow(g, (p - 1) // 2, p) != 1:
            return g

# ElGamal key generation function
def elgamal_keygen(bit_length=32):
    p = find_large_prime(bit_length)
    g = find_generator(p)
    private_key = random.randint(1, p - 2)
    public_key = pow(g, private_key, p)
    return private_key, public_key, p, g

# ElGamal encryption function for a single integer message
def elgamal_encrypt(p, g, public_key, message):
    k = random.randint(1, p - 2)
    c1 = pow(g, k, p)
    c2 = (message * pow(public_key, k, p)) % p
    return c1, c2

# ElGamal decryption function for a single encrypted message
def elgamal_decrypt(p, private_key, c1, c2):
    s = pow(c1, private_key, p)
    s_inv = mod_inverse(s, p)
    m = (c2 * s_inv) % p
    return m

# Encrypt a list of integers using ElGamal
def elgamal_encrypt_list(p, g, public_key, message_list):
    encrypted_list = []
    for message in message_list:
        encrypted_list.append(elgamal_encrypt(p, g, public_key, message))
    return encrypted_list

# Decrypt a list of encrypted messages using ElGamal
def elgamal_decrypt_list(p, private_key, encrypted_list):
    decrypted_list = []
    for c1, c2 in encrypted_list:
        decrypted_list.append(elgamal_decrypt(p, private_key, c1, c2))
    return decrypted_list

if __name__ == '__main__':
    private_key, public_key, p, g = elgamal_keygen(32)
    print(f"Public Key: {public_key}")
    print(f"Private Key: {private_key}")
    print(f"Prime (p): {p}")
    print(f"Generator (g): {g}")

    message = 1234567890
    c1, c2 = elgamal_encrypt(p, g, public_key, message)
    print(f"Encrypted message: (c1: {c1}, c2: {c2})")

    decrypted_message = elgamal_decrypt(p, private_key, c1, c2)
    print(f"Decrypted message: {decrypted_message}")
