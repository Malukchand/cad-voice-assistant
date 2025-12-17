# main.py
# Phase 2: CAD Voice Assistant with Modifications (Scale, Move, Delete, Resize)
# Flow: voice → AI (interpret) → Action (Modify + Update Viewer) → AI (Confirm)

import os
import threading
import whisper

from cad.loader import load_step_shape
from cad.info import create_cad_summary
from cad.features import show_shape, start_viewer_loop, create_feature_summary, find_cylindrical_faces
from cad.modify import scale_shape, translate_shape, delete_solid, resize_cylindrical_feature

from voice.record_basic import record_audio
from voice.tts_basic import speak
from ai.cad_command_interpreter import interpret_command, answer_question

def run_viewer(shape):
    """
    Separate thread: open the 3D viewer and show the shape.
    """
    show_shape(shape)
    start_viewer_loop()   # blocks this thread (GUI loop)

def generate_full_summary(shape):
    """Refreshes the CAD summary strings from the current shape."""
    basic = create_cad_summary(shape)
    feat = create_feature_summary(shape)
    return basic + "\n\nFEATURES:\n" + feat

def main():
    # 1) Choose CAD model
    path = input("Enter STEP file path (blank = model.stp): ").strip()
    if not path:
        path = "model.stp"

    if not os.path.exists(path):
        print(f"ERROR: File '{path}' not found.")
        return

    print(f"Loading CAD model: {path}")
    shape = load_step_shape(path)

    # 2) Build initial CAD summary
    cad_full_summary = generate_full_summary(shape)

    print("CAD summary for AI:\n")
    print(cad_full_summary)
    print("\n--- 3D viewer starting ---\n")

    # 3) Start 3D viewer in background thread
    viewer_thread = threading.Thread(
        target=run_viewer, args=(shape,), daemon=True
    )
    viewer_thread.start()

    # 4) Load Whisper model
    print("Loading Whisper model...")
    whisper_model = whisper.load_model("small")

    speak("CAD voice assistant ready. You can ask questions or say 'scale', 'move', 'delete', or 'resize hole'.")

    # 5) Main voice loop
    while True:
        input("Press ENTER and then speak...")

        # Record voice to file
        record_audio("voice_cmd.wav", 5)

        # Transcribe voice → text
        result = whisper_model.transcribe("voice_cmd.wav", language="en")
        user_text = result["text"].strip()
        print("You said:", user_text)

        if not user_text:
            continue

        # Exit commands
        if user_text.lower() in ("exit", "quit", "stop"):
            speak("Okay, goodbye.")
            break

        # A) Interpret the intent
        cmd_data = interpret_command(user_text)
        command = cmd_data.get("command", "UNKNOWN")
        print(f"Interpreted Command: {cmd_data}")

        # B) Execute Command
        modified = False
        response_text = ""

        try:
            if command == "SCALE":
                factor = cmd_data.get("factor", 1.0)
                shape = scale_shape(shape, factor)
                modified = True
                response_text = f"Scaled the model by a factor of {factor}."

            elif command == "MOVE":
                dx = cmd_data.get("dx", 0.0)
                dy = cmd_data.get("dy", 0.0)
                dz = cmd_data.get("dz", 0.0)
                shape = translate_shape(shape, dx, dy, dz)
                modified = True
                response_text = f"Moved the model by X {dx}, Y {dy}, Z {dz}."

            elif command == "DELETE":
                idx = cmd_data.get("index", -1)
                shape = delete_solid(shape, idx)
                modified = True
                if idx == -1:
                    response_text = "Deleted the selected solid."
                else:
                    response_text = f"Deleted solid number {idx}."

            elif command == "RESIZE_FEATURE":
                # Find the feature (cylinder) to resize
                ftype = cmd_data.get("feature_type", "hole")
                idx = cmd_data.get("index", 0)
                
                # Get all cylinders again to find the one at 'idx'
                # Note: This is a bit fragile if list order changes, but okay for prototype
                cyls = find_cylindrical_faces(shape)
                if idx < 0 or idx >= len(cyls):
                    speak(f"I assume you mean the first {ftype}.")
                    idx = 0
                
                if not cyls:
                    response_text = f"No {ftype}s found to resize."
                else:
                    target_face = cyls[idx]['face']
                    
                    if "new_radius" in cmd_data:
                        new_r = cmd_data["new_radius"]
                        shape = resize_cylindrical_feature(shape, target_face, new_r)
                        modified = True
                        response_text = f"Resized {ftype} {idx} to radius {new_r}."
                    elif "scale" in cmd_data:
                        # Calculate new radius based on scale
                        current_r = cyls[idx]['radius']
                        new_r = current_r * cmd_data["scale"]
                        shape = resize_cylindrical_feature(shape, target_face, new_r)
                        modified = True
                        response_text = f"Resized {ftype} {idx} by scale {cmd_data['scale']}."
                    else:
                        response_text = "I didn't get a new size for the feature."

            elif command == "QUESTION":
                # Answer question using CURRENT summary
                answer = answer_question(cad_full_summary, user_text)
                response_text = answer

            else: # UNKNOWN or fallback
                # Fallback to general Q&A if it looks like a question, otherwise apologize
                # For now, let's just try to answer it.
                answer = answer_question(cad_full_summary, user_text)
                response_text = answer

        except Exception as e:
            print(f"Error executing command: {e}")
            response_text = "I ran into an error trying to do that."

        # C) Update System State if modified
        if modified:
            # 1. Update 3D Viewer
            print("Updating viewer...")
            show_shape(shape)
            
            # 2. Update CAD Summary (context for next turn)
            cad_full_summary = generate_full_summary(shape)

        # D) Speak Response
        if response_text:
            print("Assistant:", response_text)
            speak(response_text)


if __name__ == "__main__":
    main()
