import pyaudio
import numpy as np
import time

indexes = [2, 7, 11, 14]

pa = pyaudio.PyAudio()

for idx in indexes:
    print("\nTesting device:", idx)

    try:
        stream = pa.open(format=pyaudio.paInt16,
                         channels=1,
                         rate=44100,
                         input=True,
                         input_device_index=idx,
                         frames_per_buffer=1024)

        print("Listening for 2 seconds...")
        for _ in range(20):
            data = np.frombuffer(stream.read(1024), dtype=np.int16)
            print("Volume:", np.abs(data).mean())
            time.sleep(0.1)

        stream.close()

    except Exception as e:
        print("❌ Error:", e)
