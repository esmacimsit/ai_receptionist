import os
import sys

# Bu dosyanın (main.py) olduğu yeri tam adres olarak alıyor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# stt klasörünün tam yolunu oluşturuyor (/Users/esma/.../stt gibi)
STT_DIR = os.path.join(BASE_DIR, "stt")

def main():
    print("\n" + "="*40)
    print("   🚀 AI RECEPTIONIST LAUNCHER")
    print("="*40)
    print(" [t] TURKISH MODE (Only TR) - 0.13s")
    print(" [b] GLOBAL MODE (TR + EN) - 0.24s")
    print("-" * 40)

    choice = input(">>> Select (t/b): ").strip().lower()

    if choice == 't':
        print("\n[SYSTEM] Launching: TURKISH MODE...")
        # sys.executable = Senin aktif venv python'ın
        os.system(f"{sys.executable} {os.path.join(STT_DIR, 'only_tr.py')}")

    elif choice == 'b':
        print("\n[SYSTEM] Launching: GLOBAL MODE...")
        os.system(f"{sys.executable} {os.path.join(STT_DIR, 'eng_tr.py')}")

    else:
        print("[ERROR] Invalid selection. Exiting.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Exit.")