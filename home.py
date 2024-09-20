from flask import Flask, request, jsonify, send_file, render_template
import os
import wave
import struct
import Audio
import Elgamal
import magic
import numpy as np

app = Flask(__name__)

# Directory setup
ENCRYPTED_DIR = 'encrypted_files'
DECRYPTED_DIR = 'decrypted_files'
PARAMS_FILE = 'audio_params.txt'

# Ensure directories exist
os.makedirs(ENCRYPTED_DIR, exist_ok=True)
os.makedirs(DECRYPTED_DIR, exist_ok=True)

# In-memory storage for keys
keys = {}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/real')
def real():
    return render_template('real.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

# Key generation
@app.route('/generate-keys', methods=['GET'])
def generate_keys():
    private_key, public_key, p, g = Elgamal.elgamal_keygen(128)
    keys['private_key'] = private_key
    keys['public_key'] = public_key
    keys['p'] = p
    keys['g'] = g
    return jsonify({
        'public_key': str(public_key),
        'private_key': str(private_key)
    })

# Audio to integers conversion
@app.route('/convert-to-integers', methods=['POST'])
def convert_to_integers():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    file_path = os.path.join(ENCRYPTED_DIR, audio_file.filename)
    audio_file.save(file_path)

    # Convert audio to binary
    binary_data, params = Audio.audio_to_binary(file_path)

    # Save audio parameters for later use
    with open(os.path.join(ENCRYPTED_DIR, PARAMS_FILE), 'w') as param_file:
        param_file.write(f"{params.nchannels} {params.sampwidth} {params.framerate} {params.nframes}")

    # Adjust audio samples before encryption (range 0-65535)
    adjusted_data = [sample + 32768 for sample in binary_data]

    # Save the adjusted binary data to a file
    binary_file_path = os.path.join(ENCRYPTED_DIR, 'binary_data.txt')
    with open(binary_file_path, 'w') as f:
        for item in adjusted_data:
            f.write(f"{item}\n")

    return jsonify({'success': True})

# Encryption
@app.route('/encrypt-audio', methods=['GET'])
def encrypt_audio():
    if 'public_key' not in keys or 'private_key' not in keys:
        return jsonify({'error': 'Keys not generated yet'}), 400

    public_key = keys['public_key']
    p = keys['p']
    g = keys['g']

    encrypted_data = []
    
    # Read the binary data from file
    binary_file_path = os.path.join(ENCRYPTED_DIR, 'binary_data.txt')
    if not os.path.exists(binary_file_path):
        return jsonify({'error': 'No binary data found. Please convert audio first.'}), 400
    
    with open(binary_file_path, 'r') as f:
        binary_data = [int(line.strip()) for line in f.readlines()]
    
    # Encrypt each integer
    for message in binary_data:
        c1, c2 = Elgamal.elgamal_encrypt(p, g, public_key, message)
        encrypted_data.append((c1, c2))
    
    # Save encrypted data to a file
    encrypted_file_path = os.path.join(ENCRYPTED_DIR, 'encrypted_data.txt')
    with open(encrypted_file_path, 'w') as f:
        for c1, c2 in encrypted_data:
            f.write(f"{c1} {c2}\n")
    
    return jsonify({'success': True})

# Decryption
@app.route('/decrypt-audio', methods=['POST'])
def decrypt_audio():
    private_key = int(request.form['private_key'])
    p = keys['p']

    decrypted_data = []

    # Load encrypted data from file
    encrypted_file = request.files['encrypted_file']
    file_path = os.path.join(DECRYPTED_DIR, encrypted_file.filename)
    encrypted_file.save(file_path)

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        encrypted_data = []
        for line in f:
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            try:
                c1, c2 = map(int, parts)
                encrypted_data.append((c1, c2))
            except ValueError:
                continue

    if not encrypted_data:
        return jsonify({'error': 'No valid encrypted data found.'}), 400

    # Decrypt each data point
    for c1, c2 in encrypted_data:
        message = Elgamal.elgamal_decrypt(p, private_key, c1, c2)
        decrypted_data.append(message)

    # Adjust back to original range after decryption
    adjusted_data = [int(message - 32768) for message in decrypted_data]

    # Save decrypted integers to file for converting back to audio
    decrypted_file_path = os.path.join(DECRYPTED_DIR, 'decrypted_data.txt')
    with open(decrypted_file_path, 'w') as f:
        for message in adjusted_data:
            f.write(f"{message}\n")
    
    return jsonify({'success': True})

# Convert decrypted data to audio
@app.route('/convert-to-audio', methods=['GET'])
def convert_to_audio():
    decrypted_file_path = os.path.join(DECRYPTED_DIR, 'decrypted_data.txt')

    if not os.path.exists(decrypted_file_path):
        return jsonify({'error': 'No decrypted data found.'}), 400
    
    with open(decrypted_file_path, 'r') as f:
        decrypted_data = [int(line.strip()) for line in f]

    # Load the original parameters
    param_path = os.path.join(ENCRYPTED_DIR, PARAMS_FILE)
    with open(param_path, 'r') as param_file:
        nchannels, sampwidth, framerate, nframes = map(int, param_file.read().split())
        params = wave._wave_params(nchannels, sampwidth, framerate, nframes, 'NONE', 'not compressed')

    # Convert back to audio
    decrypted_audio_path = os.path.join(DECRYPTED_DIR, 'decrypted_audio.wav')
    Audio.binary_to_audio(decrypted_data, params, decrypted_audio_path)

    return send_file(decrypted_audio_path, as_attachment=True)

# Route to display the SNR page
@app.route('/snr')
def snr():
    return render_template('snr.html')

# Function to check if the file is a valid WAV file
def is_valid_wave(file_path):
    try:
        with wave.open(file_path, 'rb') as wave_file:
            # Check that the file has basic WAV properties
            params = wave_file.getparams()
            if params.nchannels > 0 and params.sampwidth > 0 and params.framerate > 0:
                return True
    except wave.Error:
        return False
    return False

# Function to calculate SNR
def compute_snr(original_path, decrypted_path):
    with wave.open(original_path, 'rb') as original_wave:
        original_data = np.frombuffer(original_wave.readframes(-1), dtype=np.int16)
    
    with wave.open(decrypted_path, 'rb') as decrypted_wave:
        decrypted_data = np.frombuffer(decrypted_wave.readframes(-1), dtype=np.int16)
    
    if len(original_data) != len(decrypted_data):
        raise ValueError("The original and decrypted files have different lengths.")
    
    noise = original_data - decrypted_data
    signal_power = np.sum(original_data ** 2)
    noise_power = np.sum(noise ** 2)
    
    if noise_power == 0:
        return float('inf')  # Infinite SNR means no noise
    
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

# SNR calculation route
@app.route('/calculate-snr', methods=['POST'])
def calculate_snr():
    # Save the files temporarily for processing
    original_file = request.files['original_file']
    decrypted_file = request.files['decrypted_file']
    
    # Ensure the 'temp' directory exists
    temp_dir = 'temp'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)  # Create 'temp' directory if it doesn't exist
    
    original_path = os.path.join(temp_dir, 'original.wav')
    decrypted_path = os.path.join(temp_dir, 'decrypted.wav')
    
    # Save files to temp folder
    original_file.save(original_path)
    decrypted_file.save(decrypted_path)
    
    # Validate if the files are valid WAV audio files
    if not is_valid_wave(original_path) or not is_valid_wave(decrypted_path):
        # Delete the files if they are not valid
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(decrypted_path):
            os.remove(decrypted_path)
        return jsonify({'error': 'Both files must be valid WAV format.'}), 400
    
    try:
        # Calculate SNR
        snr_value = compute_snr(original_path, decrypted_path)
        # Convert 'inf' or '-inf' to string for valid JSON
        if np.isinf(snr_value):
            snr_value = "Infinity" if snr_value > 0 else "-Infinity"
        
        result = jsonify({'snr': snr_value})
        
        # After calculation, remove the temporary files
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(decrypted_path):
            os.remove(decrypted_path)
        
        return result
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'An error occurred during SNR calculation.'}), 500
    finally:
        # Ensure files are deleted in case of an error as well
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(decrypted_path):
            os.remove(decrypted_path)

if __name__ == '__main__':
    app.run(debug=True)
