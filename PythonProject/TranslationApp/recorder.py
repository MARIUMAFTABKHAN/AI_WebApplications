import sounddevice as sd
from scipy.io.wavfile import write
import datetime

def record_from_line_in(duration=10, device_index=5):
    print(f"🎤 Recording from Line-In (device {device_index})...")

    fs = 16000  # Whisper recommended sample rate

    audio = sd.rec(
        int(duration * fs),
        samplerate=fs,
        channels=1,
        dtype='int16',
        device=device_index
    )
    sd.wait()

    filename = f"linein_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    write(filename, fs, audio)

    print(f"✔ Saved audio: {filename}")
    return filename
