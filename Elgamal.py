import random
from sympy import randprime, mod_inverse

# Function to generate large prime using sympy
def find_large_prime(bit_length=128):
    return randprime(2**(bit_length-1), 2**bit_length)

# Function to find a generator for prime p
def find_generator(p):
    for g in range(2, p):
        if pow(g, 2, p) != 1 and pow(g, (p - 1) // 2, p) != 1:
            return g
    raise ValueError(f"No generator found for prime {p}")

# ElGamal key generation
def elgamal_keygen(bit_length=128):
    p = find_large_prime(bit_length)
    g = find_generator(p)
    private_key = random.randint(1, p - 2)
    public_key = pow(g, private_key, p)
    return private_key, public_key, p, g

# ElGamal encryption
def elgamal_encrypt(p, g, public_key, message):
    k = random.randint(1, p - 2)
    c1 = pow(g, k, p)
    c2 = (message * pow(public_key, k, p)) % p
    return c1, c2

# ElGamal decryption
def elgamal_decrypt(p, private_key, c1, c2):
    s = pow(c1, private_key, p)
    s_inv = mod_inverse(s, p)
    m = (c2 * s_inv) % p
    return m

if __name__ == '__main__':
    private_key, public_key, p, g = elgamal_keygen(128)
    print(f"Public Key: {public_key}")
    print(f"Private Key: {private_key}")
    print(f"Prime (p): {p}")
    print(f"Generator (g): {g}")

    message = 1234567890
    c1, c2 = elgamal_encrypt(p, g, public_key, message)
    print(f"Encrypted message: (c1: {c1}, c2: {c2})")

    decrypted_message = elgamal_decrypt(p, private_key, c1, c2)
    print(f"Decrypted message: {decrypted_message}")
