import sounddevice as sd
import soundfile as sf

def record_loopback(duration=5, filename="loopback.wav"):
    output = sd.query_devices(kind='output')
    device_index = output['index']

    print("Using device index:", device_index)

    samplerate = 44100
    channels = output['max_output_channels']

    with sf.SoundFile(filename, mode='w', samplerate=samplerate, channels=channels) as file:
        stream = sd.InputStream(
            samplerate=samplerate,
            device=device_index,
            channels=channels,
            dtype='float32',
            blocksize=2048,
            extra_settings=sd.WasapiSettings(exclusive=False)  # ❗ old method
        )
        stream.start()
        sd.sleep(duration * 1000)
        stream.stop()

    print("Saved:", filename)


record_loopback()
