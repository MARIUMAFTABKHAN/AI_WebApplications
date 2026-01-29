import speech_recognition as sr
from deep_translator import GoogleTranslator

AUDIO_DEVICE_INDEX = 1  # try 1 → then 6 → then 11

recognizer = sr.Recognizer()
translator = GoogleTranslator(source="auto", target="en")

print("\n🎤 Urdu → English Live Translation Started...")
print("▶ Play your Urdu YouTube video now.")
print("-----------------------------------------------------\n")

while True:
    with sr.Microphone(device_index=AUDIO_DEVICE_INDEX) as source:
        print("🎧 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, phrase_time_limit=5)

        try:
            print("📝 Transcribing Urdu audio...")
            urdu_text = recognizer.recognize_google(audio, language="ur-PK")
            print(f"Urdu: {urdu_text}")

            english = translator.translate(urdu_text)
            print(f"English: {english}")
            print("-----------------------------------------------------\n")

        except sr.UnknownValueError:
            print("⚠ Could not understand audio, skipping...\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")
