import wave
import struct
import random
import os

# Logging functionality to capture messages and save in a log file
def log_message(message, log_file):
    print(message)
    with open(log_file, 'a') as f:
        f.write(message + '\n')

# Function to generate a large prime number (ElGamal setup)
def find_large_prime(bit_length=32, log_file=''):
    log_message("Generating a large prime number...", log_file)
    
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
        if is_prime(p_candidate):
            log_message(f"Large prime found: {p_candidate}", log_file)
            return p_candidate

# Function to find a generator for the prime p
def find_generator(p, log_file=''):
    log_message("Finding generator for prime number...", log_file)
    for g in range(2, p):
        if pow(g, 2, p) != 1 and pow(g, (p - 1) // 2, p) != 1:
            log_message(f"Generator found: {g}", log_file)
            return g

# Function to generate private and public keys
def generate_keys(p, g, log_file=''):
    log_message("Generating public and private key pair...", log_file)
    private_key = random.randint(1, p - 1)
    public_key = pow(g, private_key, p)
    log_message(f"Private key: {private_key}, Public key: {public_key}", log_file)
    return private_key, public_key

# ElGamal encryption for a single message
def elgamal_encrypt(p, g, public_key, message):
    k = random.randint(1, p - 2)
    c1 = pow(g, k, p)
    c2 = (message * pow(public_key, k, p)) % p
    return c1, c2

# ElGamal decryption for a single message
def elgamal_decrypt(p, private_key, c1, c2):
    s = pow(c1, private_key, p)
    s_inv = pow(s, p - 2, p)
    m = (c2 * s_inv) % p
    return m

# Function to convert audio to binary integers
def audio_to_binary(audio_file, log_file=''):
    log_message(f"Converting audio file '{audio_file}' to binary...", log_file)
    with wave.open(audio_file, 'rb') as wave_file:
        params = wave_file.getparams()
        audio_data = wave_file.readframes(wave_file.getnframes())
        binary_data = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)
    log_message(f"Extracted {len(binary_data)} samples from audio.", log_file)
    return binary_data, params

# Function to convert binary data back to audio and save as a WAV file
def binary_to_audio(binary_data, params, audio_file, log_file=''):
    log_message(f"Converting binary data back to audio and saving as '{audio_file}'...", log_file)
    try:
        audio_data = struct.pack('<' + 'h' * len(binary_data), *binary_data)
    except struct.error as e:
        log_message(f"Error in packing data: {e}", log_file)
        binary_data = [max(-32768, min(32767, value)) for value in binary_data]
        audio_data = struct.pack('<' + 'h' * len(binary_data), *binary_data)
    
    with wave.open(audio_file, 'wb') as wave_file:
        wave_file.setparams(params)
        wave_file.writeframes(audio_data)
    log_message(f"Written {len(binary_data)} samples to '{audio_file}'.", log_file)

# Function to encrypt audio file and save as encrypted text
def encrypt_audio_file(input_file, encrypted_file, log_file):
    p = find_large_prime(32, log_file)
    g = find_generator(p, log_file)
    
    log_message(f"Prime number (p): {p}, Generator (g): {g}", log_file)
    
    # Generate keys
    private_key, public_key = generate_keys(p, g, log_file)

    # Convert audio to binary
    binary_data, params = audio_to_binary(input_file, log_file)

    # Adjust sample values to be in range [0, 65535]
    adjusted_data = [sample + 32768 for sample in binary_data]

    # Encrypt the binary data
    encrypted_data = []
    log_message("Encrypting binary data...", log_file)
    for message in adjusted_data:
        c1, c2 = elgamal_encrypt(p, g, public_key, message)
        encrypted_data.append((c1, c2))
    
    # Save encrypted data to a text file
    log_message(f"Saving encrypted data to '{encrypted_file}'...", log_file)
    with open(encrypted_file, 'w') as f:
        for c1, c2 in encrypted_data:
            f.write(f'{c1} {c2}\n')

    return p, g, private_key, public_key, params

# Function to decrypt audio file from encrypted text
def decrypt_audio_file(encrypted_file, p, private_key, params, decrypted_file, log_file):
    log_message("Loading encrypted data for decryption...", log_file)
    with open(encrypted_file, 'r') as f:
        encrypted_data = []
        for line in f:
            c1, c2 = map(int, line.strip().split())
            encrypted_data.append((c1, c2))

    decrypted_data = []
    log_message("Decrypting binary data...", log_file)
    for c1, c2 in encrypted_data:
        message = elgamal_decrypt(p, private_key, c1, c2)
        decrypted_data.append(message)

    # Adjust decrypted sample values back to original range
    recovered_data = [int(message - 32768) for message in decrypted_data]

    # Convert binary back to audio
    binary_to_audio(recovered_data, params, decrypted_file, log_file)

def main():
    # Define paths and file names
    log_file = 'terminal_output.txt'
    input_file = input("Enter the path to the WAV audio file: ")
    encrypted_file = 'encrypted_data.txt'
    decrypted_file = 'decrypted_output.wav'

    # Remove old log file if it exists
    if os.path.exists(log_file):
        os.remove(log_file)

    log_message("Starting ElGamal encryption program...", log_file)

    # Encrypt the audio file
    p, g, private_key, public_key, params = encrypt_audio_file(input_file, encrypted_file, log_file)

    log_message("Encryption completed.", log_file)

    # Decrypt the audio file
    decrypt_audio_file(encrypted_file, p, private_key, params, decrypted_file, log_file)

    log_message("Decryption completed.", log_file)

if __name__ == '__main__':
    main()
