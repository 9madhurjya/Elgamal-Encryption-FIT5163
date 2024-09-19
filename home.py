from flask import Flask, request, jsonify, send_file, render_template
import os
import wave
import Audio
import Elgamal

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

# Common functions for key generation, conversion, encryption, decryption
@app.route('/generate-keys', methods=['GET'])
def generate_keys():
    private_key, public_key, p, g = Elgamal.elgamal_keygen(32)
    keys['private_key'] = private_key
    keys['public_key'] = public_key
    keys['p'] = p
    keys['g'] = g
    return jsonify({
        'public_key': public_key,
        'private_key': private_key
    })

@app.route('/convert-to-integers', methods=['POST'])
def convert_to_integers():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    file_path = os.path.join(ENCRYPTED_DIR, audio_file.filename)
    audio_file.save(file_path)

    # Convert audio to integers
    binary_data, params = Audio.audio_to_binary(file_path)

    # Save audio parameters for later use
    with open(os.path.join(ENCRYPTED_DIR, PARAMS_FILE), 'w') as param_file:
        param_file.write(f"{params.nchannels} {params.sampwidth} {params.framerate} {params.nframes}")

    # Save the binary data to a file for encryption
    binary_file_path = os.path.join(ENCRYPTED_DIR, 'binary_data.txt')
    with open(binary_file_path, 'w') as f:
        for item in binary_data:
            f.write(f"{item}\n")

    return jsonify({'success': True})

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
        encrypted_data = [tuple(map(int, line.strip().split())) for line in f]

    # Decrypt each data point
    for c1, c2 in encrypted_data:
        message = Elgamal.elgamal_decrypt(p, private_key, c1, c2)
        decrypted_data.append(message)
    
    # Save decrypted integers to file for converting back to audio
    decrypted_file_path = os.path.join(DECRYPTED_DIR, 'decrypted_data.txt')
    with open(decrypted_file_path, 'w') as f:
        for message in decrypted_data:
            f.write(f"{message}\n")
    
    return jsonify({'success': True})

@app.route('/convert-to-audio', methods=['GET'])
def convert_to_audio():
    decrypted_file_path = os.path.join(DECRYPTED_DIR, 'decrypted_data.txt')

    # Load decrypted data
    if not os.path.exists(decrypted_file_path):
        return jsonify({'error': 'No decrypted data found. Please decrypt audio first.'}), 400
    
    with open(decrypted_file_path, 'r') as f:
        decrypted_data = [int(line.strip()) for line in f]

    # Load the original parameters
    param_path = os.path.join(ENCRYPTED_DIR, PARAMS_FILE)
    with open(param_path, 'r') as param_file:
        nchannels, sampwidth, framerate, nframes = map(int, param_file.read().split())
        params = wave._wave_params(nchannels, sampwidth, framerate, nframes, 'NONE', 'not compressed')

    # Adjust decrypted data back to original range
    adjusted_data = [int(sample - 32768) for sample in decrypted_data]

    # Convert back to audio file
    decrypted_audio_path = os.path.join(DECRYPTED_DIR, 'decrypted_audio.wav')
    Audio.binary_to_audio(adjusted_data, params, decrypted_audio_path)

    return send_file(decrypted_audio_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
