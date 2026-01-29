from faster_whisper import WhisperModel

def load_model():
    print("🧠 Loading Whisper model (small)...")
    model = WhisperModel("models/small", device="cpu")

    print("✔ Whisper model loaded")
    return model


def urdu_to_english(audio_file):
    model = load_model()
    print("📝 Translating Urdu → English...")
    segments, _ = model.transcribe(audio_file, task="translate")
    return " ".join([s.text for s in segments])
