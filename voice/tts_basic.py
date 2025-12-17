from gtts import gTTS
from playsound import playsound
import tempfile

def speak(text, lang="en"):
    if not text:
        return

    # Create temporary mp3
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        path = fp.name

    # Generate speech
    tts = gTTS(text=text, lang=lang)
    tts.save(path)

    # Return path for external player
    return path
