import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import time

# --- CONFIG ---
FS = 16000
MODEL_SIZE = "small"
SILENCE_DURATION = 1.2
THRESHOLD = 0.025 
BLOCKSIZE = 1024  

print(f"Model ({MODEL_SIZE}) yükleniyor... M4 Pro motorları ateşlendi!")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def rms(x):
    return float(np.sqrt(np.mean(np.square(x), dtype=np.float32)))

def listen_until_silent():
    print("\n[BEKLEMEDE] Başlamak için ENTER...")
    input()

    print(">>> Dinliyorum... (TR/EN)")
    audio_data = []
    callback_done = False
    silent_limit = int(SILENCE_DURATION * FS / BLOCKSIZE)

    def callback(indata, frames, time, status):
        nonlocal callback_done
        if status:
            print(f"Ses Hatası: {status}") # Olası donanım hatalarını yakala
        
        audio_data.append(indata.copy())

        if rms(indata) < THRESHOLD:
            callback.silent_chunks += 1
        else:
            callback.silent_chunks = 0

        if callback.silent_chunks >= silent_limit:
            callback_done = True
            raise sd.CallbackStop

    callback.silent_chunks = 0

    with sd.InputStream(samplerate=FS, channels=1, dtype="float32", blocksize=BLOCKSIZE, callback=callback):
        while not callback_done:
            sd.sleep(50)

    audio_np = np.concatenate(audio_data, axis=0).reshape(-1)

    if audio_np.size < FS * 0.4: # Minimum süreyi 0.4'e çektim, daha güvenli
        print("[SİSTEM]: Kayıt çok kısa, atlandı.")
        return

    print("Anlamlandırılıyor...")
    start_time = time.time() # Hız testi başlıyor
    
    segments, _ = model.transcribe(
        audio_np,
        language=None,
        beam_size=5,
        vad_filter=True,
        # Halüsinasyonları engellemek için boş tokenleri bastırıyoruz
        suppress_tokens=[-1], 
        initial_prompt="Turkish, English."
    )

    full_text = "".join(s.text for s in segments).strip()
    end_time = time.time() # Hız testi bitti

    if full_text:
        print("-" * 30)
        print(f"DUYULAN: {full_text}")
        print(f"HIZ: {end_time - start_time:.2f} saniye") # Performans ölçümü
        print("-" * 30)
    else:
        print("[SİSTEM]: Ses algılandı ama metin üretilemedi.")

try:
    while True:
        listen_until_silent()
except KeyboardInterrupt:
    print("\nSistem kapatıldı.")