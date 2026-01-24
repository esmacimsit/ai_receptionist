import numpy as np
import sounddevice as sd
import time
import platform
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# --- CORE CONFIGURATION ---
FS = 16000
MODEL_SIZE = "small"   
SILENCE_DURATION = 2.5  
THRESHOLD = 0.045       
BLOCKSIZE = 1024  

# --- HARDWARE DETECTION ---
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
        mlx_whisper.transcribe(np.zeros(16000), path_or_hf_repo=f"mlx-community/whisper-{MODEL_SIZE}-mlx")
        print("[SYSTEM] Engine Ready.")
    else:
        from faster_whisper import WhisperModel
        fw_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=8)

def transcribe_audio(audio_np):
    text = ""
    
    # --- PROMPT İLE DİL KISITLAMA (Sadece TR/EN Odaklı) ---
    # Whisper'a "Sadece bu dilleri bekle" dedik. Bu, taramayı hızlandırır ve hatayı önler.
    BIASED_PROMPT = "This is a conversation in Turkish or English. Türkçe veya İngilizce konuşuluyor."

    if USE_MLX:
        import mlx_whisper
        try:
            result = mlx_whisper.transcribe(
                audio_np,
                path_or_hf_repo=f"mlx-community/whisper-{MODEL_SIZE}-mlx",
                language=None,                # Auto-Detect (Ama prompt ile yönlendirilmiş)
                fp16=True,                    
                initial_prompt=BIASED_PROMPT, # <--- İŞTE BU SATIR KİLİT NOKTA
                condition_on_previous_text=False, 
                no_speech_threshold=0.6,      
                logprob_threshold=-1.0,       
                compression_ratio_threshold=2.4,
                temperature=0.0               
            )
            text = result.get("text", "").strip()
        except Exception:
            return ""
    else:
        # Fallback
        segments, _ = fw_model.transcribe(audio_np, language=None, initial_prompt=BIASED_PROMPT, beam_size=1)
        text = "".join(s.text for s in segments).strip()

    # --- SECURITY FIREWALL ---
    text_lower = text.lower()
    
    # 1. HALLUCINATION FILTER
    yasakli_listesi = [
        # TR
        "abone ol", "beğenmeyi", "bildirimleri", "kanalımıza", 
        "izlediğiniz için", "altyazı", "konuşma devam ediyor",
        # EN
        "subscribe", "like and subscribe", "copyright", "subtitle", 
        "captioned by", "watching", "next video", "amara.org"
    ]
    
    for yasak in yasakli_listesi:
        if yasak in text_lower:
            return "" 

    # 2. LOOP BREAKER
    if len(text) > 30:
        words = text.split()
        unique_words = set(words)
        ratio = len(unique_words) / len(words) 
        if ratio < 0.2:
            return ""

    # 3. SHORT AUDIO FILTER
    if len(text) < 2:
        return ""
            
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
            sd.sleep(50)

    audio_np = np.concatenate(audio_data, axis=0).reshape(-1).astype(np.float32)
    
    if np.max(np.abs(audio_np)) > 0:
        audio_np = audio_np / np.max(np.abs(audio_np))
    
    if np.sum(np.abs(audio_np)) < 0.1:
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
        print(f"[SYSTEM] No valid speech detected.")

try:
    while True:
        listen_until_silent()
except KeyboardInterrupt:
    print("\n[SYSTEM] Shutdown.")