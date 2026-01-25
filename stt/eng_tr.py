import numpy as np
import sounddevice as sd
import time
import platform
import warnings
import re  

# Gereksiz uyarıları kapat
warnings.filterwarnings("ignore", category=RuntimeWarning)

# --- FABRİKA AYARLARI (En Stabil Hali) ---
FS = 16000
MODEL_SIZE = "small"   
SILENCE_DURATION = 2.0  
THRESHOLD = 0.045       
BLOCKSIZE = 1024  

# --- DONANIM TESPİTİ ---
USE_MLX = False
fw_model = None 

def get_backend():
    global USE_MLX
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        try:
            import mlx_whisper
            print("[SYSTEM] 🍏 Apple Silicon (M4 Pro) detected. Neural Engine active.")
            USE_MLX = True
            return "mlx"
        except ImportError:
            pass
    return "cpu"

def load_model():
    global fw_model, USE_MLX
    backend = get_backend()
    if backend == "mlx":
        print(f"[SYSTEM] Model loaded: {MODEL_SIZE}. Warming up engine...")
        import mlx_whisper
        try:
            mlx_whisper.transcribe(np.zeros(16000), path_or_hf_repo=f"mlx-community/whisper-{MODEL_SIZE}-mlx")
        except:
            pass
        print("[SYSTEM] Engine Ready.")
    else:
        from faster_whisper import WhisperModel
        fw_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=8)

def transcribe_audio(audio_np):
    text = ""
    
    # Prompt: Bias var ama faydalı bir bias.
    target_prompt = "This is a conversation in Turkish or English. Türkçe veya İngilizce konuşuluyor."
    
    if USE_MLX:
        import mlx_whisper
        try:
            result = mlx_whisper.transcribe(
                audio_np,
                path_or_hf_repo=f"mlx-community/whisper-{MODEL_SIZE}-mlx",
                language=None,                
                fp16=True,                    
                initial_prompt=target_prompt, 
                condition_on_previous_text=False, 
                no_speech_threshold=0.6,      
                logprob_threshold=-1.0,       
                compression_ratio_threshold=2.4,
                temperature=0.0               
            )
            text = result.get("text", "").strip()
        except Exception as e:
            print(f"[ERROR] Transcribe: {e}")
            return ""
    else:
        try:
            segments, _ = fw_model.transcribe(audio_np, language=None, initial_prompt=target_prompt, beam_size=1)
            text = "".join(s.text for s in segments).strip()
        except Exception as e:
            print(f"[ERROR] Transcribe: {e}")
            return ""

    # --- ESKİ GÜVENİLİR REGEX (İnsaflı Sürüm) ---
    allowed_chars = r"[a-zA-Z0-9\s\.\,\?\!\-\'\:çÇğĞıİöÖşŞüÜâÂîÎûÛ@%€$£#\(\)\"“”’&+=*]"
    
    clean_text = re.sub(allowed_chars, "", text)
    
    if len(clean_text) > 0:
        return ""

    # --- FİLTRELER ---
    text_lower = text.lower()
    yasakli_listesi = ["abone ol", "altyazı", "konuşma devam", "izlediğiniz", "subtitle", "copyright", "subscribe", "amara.org"]
    
    for yasak in yasakli_listesi:
        if yasak in text_lower: return "" 
    if len(text) < 2: return ""
            
    return text

load_model()

def rms(x):
    return float(np.sqrt(np.mean(np.square(x), dtype=np.float32)))

def listen_until_silent():
    print("\n[IDLE] Press ENTER to record...")
    input()

    print(">>> Listening... (Bilingual VAD Active)")
    audio_data = []
    callback_done = False
    silent_limit = int(SILENCE_DURATION * FS / BLOCKSIZE)

    def callback(indata, frames, time, status):
        nonlocal callback_done
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
            sd.sleep(10)

    audio_np = np.concatenate(audio_data, axis=0).reshape(-1).astype(np.float32)
    
    # --- DÜZELTME BURADA ---
    # Eğer ses çok kısıksa hem return et hem de haber ver.
    if rms(audio_np) < 0.01:
        print("[SYSTEM] Low energy noise detected (Ignored).")
        return

    print("Processing...")
    start_time = time.time()
    
    full_text = transcribe_audio(audio_np)
    latency = time.time() - start_time

    if full_text:
        print(f"-"*50)
        print(f"[TRANSCRIPT] {full_text}")
        print(f"[LATENCY]    {latency:.2f}s")
        print(f"-"*50)
    else:
        # Eğer RMS yüksekse ama Whisper "anlamsız" bulduysa burası çalışır
        print(f"[SYSTEM] No valid speech detected.")

try:
    while True:
        listen_until_silent()
except KeyboardInterrupt:
    print("\n[SYSTEM] Shutdown.")