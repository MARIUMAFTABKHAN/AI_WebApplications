import speech_recognition as sr
from transformers import pipeline
import torch

def initialize_translator():
    """
    Loads the NLLB translator model once.
    Uses GPU (CUDA) if available, otherwise defaults to CPU.
    """
    device = 0 if torch.cuda.is_available() else -1
    model_name = "facebook/nllb-200-distilled-600M"
    
    print(f"Loading NLLB translator model ({model_name})...")
    print(f"Using device: {'GPU (CUDA)' if device == 0 else 'CPU'}")
    
    try:
        translator = pipeline("translation",
                            model=model_name,
                            tokenizer=model_name,
                            device=device)
        print("Translator model loaded successfully.")
        return translator
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please ensure you have 'transformers', 'torch', and 'sentencepiece' installed.")
        return None

def main():
    # 1. Initialize models
    translator = initialize_translator()
    if translator is None:
        return

    recognizer = sr.Recognizer()

    # 2. Main listening loop
    print("\n--- Live Urdu to English Translation (Press Ctrl+C to exit) ---")
    
    while True:
        try:
            # Use the default microphone as the audio source
            with sr.Microphone() as source:
                print("\nListening for Urdu speech...")
                
                # Adjust for ambient noise to improve recognition
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for the user's input
                audio_data = recognizer.listen(source)

            print("Processing audio...")

            # 3. Transcribe audio using Whisper
            # This uses the local 'large-v3' model.
            # The first time this runs, it will download the model.
            urdu_text = recognizer.recognize_whisper(
                audio_data,
                model="large-v3",  # <-- This line is updated
                language="urdu"    # Hinting the language is Urdu
            )

            print(f"\n[URDU]: {urdu_text}")

            # 4. Translate the text using NLLB
            # We must provide the correct NLLB language codes
            # urd_Arab = Urdu (Arabic script)
            # eng_Latn = English (Latin script)
            
            translation_result = translator(
                urdu_text,
                src_lang="urd_Arab",
                tgt_lang="eng_Latn"
            )

            english_text = translation_result[0]['translation_text']
            print(f"[ENGLISH]: {english_text}")

        except sr.UnknownValueError:
            # This error means Whisper couldn't understand the audio
            print("Whisper could not understand the audio. Please try speaking again.")
        except sr.RequestError as e:
            # This error is for API-based recognizers, but good to keep
            print(f"Could not request results; {e}")
        except KeyboardInterrupt:
            print("\nExiting program.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

if __name__ == "__main__":
    main()