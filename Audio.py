import wave
import struct
import magic  # Ensure to install python-magic
import os

# Convert audio file to binary (integer) data
def is_valid_wav_file(file_path):
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_file(file_path)
    return file_mime_type == 'audio/wav' or file_mime_type == 'audio/x-wav'

def audio_to_binary(audio_file, log_file=''):
    # Ensure the file is a valid WAV file
    if not is_valid_wav_file(audio_file):
        raise ValueError("Uploaded file is not a valid WAV file.")
    
    with wave.open(audio_file, 'rb') as wave_file:
        params = wave_file.getparams()  # Store audio parameters
        audio_data = wave_file.readframes(wave_file.getnframes())
        binary_data = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)  # Convert bytes to integers
    return binary_data, params

# Convert binary (integer) data back to audio and save as a .wav file
def binary_to_audio(binary_data, params, output_file, log_file=''):
    try:
        audio_data = struct.pack('<' + 'h' * len(binary_data), *binary_data)
    except struct.error as e:
        binary_data = [max(-32768, min(32767, value)) for value in binary_data]
        audio_data = struct.pack('<' + 'h' * len(binary_data), *binary_data)

    with wave.open(output_file, 'wb') as wave_file:
        wave_file.setparams(params)  # Use original audio parameters
        wave_file.writeframes(audio_data)
