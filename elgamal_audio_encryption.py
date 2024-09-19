import wave
import struct
import random
import os

def log_message(message, log_file):
    print(message)
    with open(log_file, 'a') as f:
        f.write(message + '\n')

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

def find_generator(p, log_file=''):
    log_message("Finding generator for prime number...", log_file)
    for g in range(2, p):
        if pow(g, 2, p) != 1 and pow(g, (p - 1) // 2, p) != 1:
            log_message(f"Generator found: {g}", log_file)
            return g

def generate_keys(p, g, log_file=''):
    log_message("Generating public and private key pair...", log_file)
    private_key = random.randint(1, p - 1)
    public_key = pow(g, private_key, p)
    log_message(f"Private key: {private_key}, Public key: {public_key}", log_file)

    # Save the keys to files
    key_dir = os.path.expanduser('~/Downloads/encryption_keys/')
    os.makedirs(key_dir, exist_ok=True)
    
    with open(os.path.join(key_dir, 'private_key.txt'), 'w') as f:
        f.write(str(private_key))
    
    with open(os.path.join(key_dir, 'public_key.txt'), 'w') as f:
        f.write(str(public_key))
    
    log_message(f"Keys saved to {key_dir}", log_file)
    return private_key, public_key

def elgamal_encrypt(p, g, public_key, message):
    k = random.randint(1, p - 2)
    c1 = pow(g, k, p)
    c2 = (message * pow(public_key, k, p)) % p
    return c1, c2

def elgamal_decrypt(p, private_key, c1, c2):
    s = pow(c1, private_key, p)
    s_inv = pow(s, p - 2, p)
    m = (c2 * s_inv) % p
    return m

def audio_to_binary(audio_file, log_file=''):
    log_message(f"Converting audio file '{audio_file}' to binary...", log_file)
    with wave.open(audio_file, 'rb') as wave_file:
        params = wave_file.getparams()
        audio_data = wave_file.readframes(wave_file.getnframes())
        binary_data = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)
    log_message(f"Extracted {len(binary_data)} samples from audio.", log_file)
    return binary_data, params

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

def main():
    # Define paths
    encrypted_dir = '/Users/madhurjya/Downloads/encrypted_files/'
    decrypted_dir = '/Users/madhurjya/Downloads/decrypted_files/'
    
    # Ensure directories exist
    os.makedirs(encrypted_dir, exist_ok=True)
    os.makedirs(decrypted_dir, exist_ok=True)

    while True:
        print("\nElGamal Encryption Program - Menu")
        print("1. Encryption")
        print("2. Decryption")
        print("3. Exit")
        option = input("Select an option (1/2/3): ").strip()

        if option == '1':
            # Encryption
            input_file = input("Enter the path to the audio file to encrypt: ").strip()
            encrypted_file = os.path.join(encrypted_dir, 'encrypted_data.txt')
            log_file = os.path.join(decrypted_dir, 'terminal_output.txt')
            
            if not os.path.isfile(input_file):
                print("Audio file does not exist. Please check the path.")
                continue
            
            # Generate prime and generator
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
            
            log_message(f"Saving encrypted data to '{encrypted_file}'...", log_file)
            with open(encrypted_file, 'w') as f:
                for c1, c2 in encrypted_data:
                    f.write(f'{c1} {c2}\n')

        elif option == '2':
            # Decryption
            encrypted_file = input("Enter the path to the encrypted file: ").strip()
            private_key_file = input("Enter the path to the private key file: ").strip()
            decrypted_file = os.path.join(decrypted_dir, 'output.wav')
            log_file = os.path.join(decrypted_dir, 'terminal_output.txt')
            
            if not os.path.isfile(encrypted_file):
                print("Encrypted file does not exist. Please check the path.")
                continue
            
            if not os.path.isfile(private_key_file):
                print("Private key file does not exist. Please check the path.")
                continue

            # Read private key from file
            with open(private_key_file, 'r') as f:
                private_key = int(f.read().strip())

            # Load and decrypt the encrypted data
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

            # Compare original and decrypted audio files
            log_message("Comparing original and decrypted audio files...", log_file)
            input_file_for_comparison = input("Enter the path to the original audio file for comparison: ").strip()
            if not os.path.isfile(input_file_for_comparison):
                print("Original audio file does not exist. Please check the path.")
                continue
            
            with wave.open(input_file_for_comparison, 'rb') as wave_file1:
                with wave.open(decrypted_file, 'rb') as wave_file2:
                    audio_data1 = wave_file1.readframes(wave_file1.getnframes())
                    audio_data2 = wave_file2.readframes(wave_file2.getnframes())
                    if audio_data1 == audio_data2:
                        log_message('Decrypted audio file matches original audio file.', log_file)
                    else:
                        log_message('Decrypted audio file does not match original audio file.', log_file)
                        log_message(f"Original audio file size: {len(audio_data1)} bytes", log_file)
                        log_message(f"Decrypted audio file size: {len(audio_data2)} bytes", log_file)
                        log_message(f"First few bytes of original file: {audio_data1[:100]}", log_file)
                        log_message(f"First few bytes of decrypted file: {audio_data2[:100]}", log_file)

        elif option == '3':
            # Exit
            print("Exiting the program.")
            break
        
        else:
            print("Invalid option. Please choose 1, 2, or 3.")

if __name__ == '__main__':
    main()
