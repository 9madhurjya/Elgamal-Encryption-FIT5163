import wave
 
def audio_to_binary(audio_file_path: str) -> bytes:
    """
    Converts an audio file to binary data.
 
    Parameters:
    - audio_file_path: str
        The path to the audio file.
 
    Returns:
    - bytes:
        The binary data of the audio file.
 
    Raises:
    - FileNotFoundError:
        If the audio file does not exist at the specified path.
    """
 
    try:
        # Open the audio file in read mode
        with wave.open(audio_file_path, 'rb') as audio_file:
            # Read all the frames from the audio file
            frames = audio_file.readframes(audio_file.getnframes())
 
            # Convert the frames to binary data
            binary_data = bytes(frames)
 
            return binary_data
 
    except FileNotFoundError:
        raise FileNotFoundError(f"Audio file not found at path: {audio_file_path}")
 
# Example usage:
audio_file_path = "path/to/audio.wav"
binary_data = audio_to_binary(audio_file_path)
print(f"Binary data of audio file '{audio_file_path}': {binary_data}")