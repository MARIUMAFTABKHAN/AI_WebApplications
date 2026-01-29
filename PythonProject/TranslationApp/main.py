from recorder import record_from_line_in
from translator import urdu_to_english

def main():
    print("▶ Play your Urdu video on mobile (AUX connected)...")

    # Record from Line-In
    audio_file = record_from_line_in(duration=10, device_index=5)

    # Translate
    print("\n🔄 Translating Urdu → English...\n")
    translated_text = urdu_to_english(audio_file)

    print("==========================================")
    print("        📌 English Translation")
    print("==========================================")
    print(translated_text)
    print("==========================================")

if __name__ == "__main__":
    main()
