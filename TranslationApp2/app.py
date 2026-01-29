import os
import re
import time
import threading
from flask import Flask, jsonify, request, render_template
import speech_recognition as sr
from openai import OpenAI
import pyodbc
from queue import Queue
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

AUDIO_DEVICE_INDEX = 2

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.2
recognizer.phrase_threshold = 0.2
recognizer.non_speaking_duration = 0.2

audio_queue = Queue()

is_running = False
latest_urdu = ""
latest_english = ""
latest_summary = ""
buffered_urdu = ""
last_chunk = ""
last_audio_time = time.time()


# ----------------------------------------------------
# Urdu punctuation helper
# ----------------------------------------------------
def punctuate_urdu(text):
    text = text.strip()
    if not re.search(r"[۔.!?]$", text):
        text += "۔"
    text = re.sub(r"( اور | لیکن | تاہم | پھر | جبکہ )", r".\1", text)
    text = re.sub(r"۔+", "۔", text)
    return text


# ----------------------------------------------------
# GPT Translation (BBC Style)
# ----------------------------------------------------
def gpt_translate_with_summary(urdu_text):

    print("\n==============================")
    print("📝 Urdu Input:", urdu_text)
    print("==============================")

    prompt = f"""
You are a senior BBC journalist and translator.

TASK 1 → Translate the Urdu text into professional, concise **BBC News English**.
TASK 2 → Produce a **1–2 sentence BBC-style summary**.

STRICT FORMAT:
English: <translation>
Summary: <summary>

Urdu:
{urdu_text}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        out = resp.choices[0].message.content.strip()

        english, summary = "", ""
        for line in out.split("\n"):
            if line.startswith("English:"):
                english = line.replace("English:", "").strip()
            if line.startswith("Summary:"):
                summary = line.replace("Summary:", "").strip()

        print("📘 English:", english)
        print("📰 Summary:", summary)
        print("==============================\n")

        return english, summary

    except Exception as e:
        print("❌ GPT ERROR:", e)
        return "", ""


# ----------------------------------------------------
# Microphone Capture Thread
# ----------------------------------------------------
def audio_capture_thread():
    global is_running

    print("🎤 Microphone Listening...")

    with sr.Microphone(device_index=AUDIO_DEVICE_INDEX) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        while is_running:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=10)
                audio_queue.put(audio)
            except:
                continue


# ----------------------------------------------------
# Translation Worker Thread
# ----------------------------------------------------
def translation_worker():
    global buffered_urdu, last_audio_time
    global latest_urdu, latest_english, latest_summary
    global last_chunk, is_running

    while is_running:

        # Process batch after silence
        if buffered_urdu and time.time() - last_audio_time > 4:
            full = punctuate_urdu(buffered_urdu.strip())
            eng, summ = gpt_translate_with_summary(full)

            latest_urdu = full
            latest_english = eng
            latest_summary = summ

            buffered_urdu = ""
            continue

        try:
            audio = audio_queue.get(timeout=1)
        except:
            continue

        try:
            text = recognizer.recognize_google(audio, language="ur-PK").strip()
            print("🎧 Heard:", text)
            last_audio_time = time.time()

            if text != last_chunk:
                buffered_urdu += " " + text
                last_chunk = text

            # If long or ends with punctuation → translate immediately
            if len(buffered_urdu.split()) >= 40 or re.search(r"[۔.!?]$", buffered_urdu):
                full = punctuate_urdu(buffered_urdu.strip())
                eng, summ = gpt_translate_with_summary(full)

                latest_urdu = full
                latest_english = eng
                latest_summary = summ

                buffered_urdu = ""

        except:
            continue


# ----------------------------------------------------
# Routes
# ----------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.get("/start")
def start():
    global is_running
    is_running = True

    threading.Thread(target=audio_capture_thread, daemon=True).start()
    threading.Thread(target=translation_worker, daemon=True).start()

    return jsonify({"status": "started"})


@app.get("/stop")
def stop():
    global is_running
    is_running = False
    return jsonify({"status": "stopped"})


@app.get("/get_latest")
def get_latest():
    global latest_urdu, latest_english, latest_summary

    data = {
        "urdu": latest_urdu,
        "english": latest_english,
        "summary": latest_summary
    }

    latest_urdu = ""
    latest_english = ""
    latest_summary = ""

    return jsonify(data)


# ----------------------------------------------------
# Save to Database
# ----------------------------------------------------
def get_db():
    return pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=khi-webdbs;"
        "DATABASE=TranslationApp;"
        "UID=NcUser;"
        "PWD=New#Contact_DB_user_2003;"
    )


@app.post("/save")
def save():
    html = request.json["editor"]
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")

    urdu, eng = "", ""

    for line in text.split("\n"):
        if line.startswith("Urdu:"):
            urdu += line.replace("Urdu:", "").strip() + "\n"
        if line.startswith("English:"):
            eng += line.replace("English:", "").strip() + "\n"

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO Translations (UrduText, EnglishText) VALUES (?, ?)", (urdu, eng))
    conn.commit()
    conn.close()

    return jsonify({"saved": True})


# ----------------------------------------------------
# Run App
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="127.0.0.1")
