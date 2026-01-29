import speech_recognition as sr
from deep_translator import GoogleTranslator

AUDIO_DEVICE_INDEX = 2  # change if needed

recognizer = sr.Recognizer()

# --- IMPORTANT: Tune for sentence-based listening ---
recognizer.energy_threshold = 300  # lower → more sensitive
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8  # detect sentence pause
recognizer.non_speaking_duration = 0.3

translator = GoogleTranslator(source="ur", target="en")

print("\n🎤 Urdu → English Sentence-by-Sentence Translation")
print("▶ Play your Urdu video on Mobile via AUX.")
print("-----------------------------------------------------\n")

while True:
    try:
        with sr.Microphone(device_index=AUDIO_DEVICE_INDEX) as source:
            print("🎧 Listening for a full sentence...")
            audio = recognizer.listen(source)  # no time limit!

            print("📝 Transcribing...")
            urdu = recognizer.recognize_google(audio, language="ur-PK")
            print(f"Urdu: {urdu}")

            english = translator.translate(urdu)
            print(f"➡ English: {english}")
            print("-----------------------------------------------------\n")

    except sr.UnknownValueError:
        print("⚠ No sentence detected, waiting...\n")

    except Exception as e:
        print(f"❌ Error: {e}\n")
