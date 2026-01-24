import os
import sys

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
        # Make sure your TR file is named 'tr_mode.py'
        os.system("python only_tr.py") 
        
    elif choice == 'b':
        print("\n[SYSTEM] Launching: GLOBAL MODE...")
        # Make sure your EN/TR file is named 'global_mode.py'
        os.system("python eng_tr.py")
        
    else:
        print("[ERROR] Invalid selection. Exiting.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Exit.")