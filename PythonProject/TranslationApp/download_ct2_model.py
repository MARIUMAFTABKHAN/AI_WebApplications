from faster_whisper import download_model

print("Downloading CT2 small model...")
model_dir = download_model("small", output_dir="models")
print("Model downloaded to:", model_dir)
