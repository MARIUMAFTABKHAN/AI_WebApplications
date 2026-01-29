from flask import Flask, jsonify, request, render_template
import threading
import speech_recognition as sr
from deep_translator import GoogleTranslator
import pyodbc
from queue import Queue
from bs4 import BeautifulSoup

app = Flask(__name__)

# ---------------- MIC + TRANSLATION CONFIG -------------------

AUDIO_DEVICE_INDEX = 1  # Your working Line-In device

recognizer = sr.Recognizer()
translator = GoogleTranslator(source="ur", target="en")

# Audio Queue for Continuous Capture
audio_queue = Queue()

is_running = False
latest_urdu = ""
latest_english = ""
last_transcript = ""   # For duplicate filtering


# ---------------- 1) CONTINUOUS AUDIO CAPTURE THREAD -------------------

def audio_capture_thread():
    """Continuously capture audio without stopping microphone."""
    global is_running

    print("🎧 Starting continuous audio capture...")

    with sr.Microphone(device_index=AUDIO_DEVICE_INDEX) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        while is_running:
            try:
                print("🎙 Listening...")
                audio = recognizer.listen(source, phrase_time_limit=None)
                audio_queue.put(audio)  # push audio chunk into queue

            except Exception as e:
                print("❌ Audio Capture Error:", e)


# ---------------- 2) TRANSLATION WORKER THREAD -------------------

def translation_worker():
    """Process queued audio WITHOUT blocking microphone."""
    global latest_urdu, latest_english, last_transcript, is_running

    while is_running:
        audio = audio_queue.get()

        try:
            print("📝 Translating...")
            urdu = recognizer.recognize_google(audio, language="ur-PK")
            english = translator.translate(urdu)

            # Duplicate filtering
            if urdu == last_transcript:
                print("⚠ Duplicate ignored:", urdu)
                audio_queue.task_done()
                continue

            last_transcript = urdu
            latest_urdu = urdu
            latest_english = english

            print("✔ Urdu:", urdu)
            print("✔ English:", english)

        except sr.UnknownValueError:
            print("⚠ Could not understand, skipping...")
        except Exception as e:
            print("❌ Translation Error:", e)

        audio_queue.task_done()


# ---------------- SQL CONNECTION -------------------

def get_db():
    return pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=khi-webdbs;"
        "DATABASE=TranslationApp;"
        "UID=NcUser;"
        "PWD=New#Contact_DB_user_2003;"
    )


# ---------------- ROUTES -------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/start")
def start_translation():
    """Start audio capture + translation threads."""
    global is_running
    is_running = True

    threading.Thread(target=audio_capture_thread, daemon=True).start()

    threading.Thread(target=translation_worker, daemon=True).start()
    return jsonify({"status": "started"})


@app.get("/stop")
def stop_translation():
    """Stop translation."""
    global is_running
    is_running = False
    return jsonify({"status": "stopped"})


@app.get("/get_latest")
def get_latest():
    """Send latest Urdu & English to UI."""
    global latest_urdu, latest_english

    data = {"urdu": latest_urdu, "english": latest_english}

    # Clear after sending
    latest_urdu = ""
    latest_english = ""

    return jsonify(data)


# ---------------- SAVE TO DATABASE (PARSE EDITOR TEXT) -------------------

@app.post("/save")
def save_to_db():
    editor_html = request.json["editor"]

    soup = BeautifulSoup(editor_html, "html.parser")
    editor_text = soup.get_text("\n")

    urdu_lines = []
    english_lines = []

    for line in editor_text.split("\n"):
        line = line.strip()
        if line.startswith("Urdu:"):
            urdu_lines.append(line.replace("Urdu:", "").strip())
        elif line.startswith("English:"):
            english_lines.append(line.replace("English:", "").strip())

    urdu_full = "\n".join(urdu_lines)
    english_full = "\n".join(english_lines)

    print("\n===== Saving to DB =====")
    print("URDU:\n", urdu_full)
    print("ENGLISH:\n", english_full)
    print("========================\n")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Translations (UrduText, EnglishText)
        VALUES (?, ?)
    """, (urdu_full, english_full))
    conn.commit()
    conn.close()

    return jsonify({"saved": True})


@app.get("/test_db")
def test_db():
    try:
        conn = get_db()
        conn.close()
        return jsonify({"db": "connected"})
    except Exception as e:
        return jsonify({"db_error": str(e)})


# ---------------- MAIN RUNNER -------------------

#if __name__ == "__main__":
#    app.run(debug=True, host="0.0.0.0")

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="127.0.0.1")

