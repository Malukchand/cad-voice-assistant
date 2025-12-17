import sys
import os
from playsound import playsound

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_path = sys.argv[1]
        try:
            playsound(audio_path)
        except Exception as e:
            print(f"Error playing sound: {e}")
        finally:
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
