# voice/record_basic.py
# Simple microphone recording using PyAudio

import pyaudio
import wave

def record_audio(output_filename="output.wav", record_seconds=5, sample_rate=44100):
    """
    Record from the default microphone and save to a WAV file.
    """
    # Audio settings
    chunk = 1024            # Number of frames per buffer
    fmt = pyaudio.paInt16   # 16-bit audio
    channels = 1            # Mono

    p = pyaudio.PyAudio()

    print(f"Recording for {record_seconds} seconds... Speak now.")

    # Open stream
    stream = p.open(format=fmt,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    # Read data in chunks
    for _ in range(0, int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop & close
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Recording finished. Saving file...")

    # Save to WAV
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(fmt))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Saved recording as {output_filename}")
# voice/record_basic.py
# Simple microphone recording using PyAudio

import pyaudio
import wave

def record_audio(output_filename="output.wav", record_seconds=5, sample_rate=44100):
    """
    Record from the default microphone and save to a WAV file.
    """
    # Audio settings
    chunk = 1024            # Number of frames per buffer
    fmt = pyaudio.paInt16   # 16-bit audio
    channels = 1            # Mono

    p = pyaudio.PyAudio()

    print(f"Recording for {record_seconds} seconds... Speak now.")

    # Open stream
    stream = p.open(format=fmt,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    # Read data in chunks
    for _ in range(0, int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop & close
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Recording finished. Saving file...")

    # Save to WAV
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(fmt))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Saved recording as {output_filename}")
# voice/record_basic.py
# Simple microphone recording using PyAudio

import pyaudio
import wave

def record_audio(output_filename="output.wav", record_seconds=5, sample_rate=44100):
    """
    Record from the default microphone and save to a WAV file.
    """
    # Audio settings
    chunk = 1024            # Number of frames per buffer
    fmt = pyaudio.paInt16   # 16-bit audio
    channels = 1            # Mono

    p = pyaudio.PyAudio()

    print(f"Recording for {record_seconds} seconds... Speak now.")

    # Open stream
    stream = p.open(format=fmt,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []

    # Read data in chunks
    for _ in range(0, int(sample_rate / chunk * record_seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop & close
    stream.stop_stream()
    stream.close()
    p.terminate()

    print("Recording finished. Saving file...")

    # Save to WAV
    wf = wave.open(output_filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(fmt))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Saved recording as {output_filename}")
