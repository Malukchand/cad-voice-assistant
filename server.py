# server.py
# Backend API for CAD Voice Assistant (FastAPI)
import os

# -------- Feature Flag --------
ENABLE_HEAVY = os.getenv("ENABLE_HEAVY", "false").lower() == "true"
# ------------------------------
import networkx as nx

import os
import shutil
import uuid
import threading
# Fix for OpenMP runtime conflict (Whisper + OCC/Numpy)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import io
import networkx as nx
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import subprocess
import sys
import difflib

# Global Audio State
CURRENT_AUDIO_PROCESS = None
LAST_SPOKEN_TEXT = ""

def stop_speaking():
    global CURRENT_AUDIO_PROCESS
    if CURRENT_AUDIO_PROCESS:
        if CURRENT_AUDIO_PROCESS.poll() is None: # Still running
            CURRENT_AUDIO_PROCESS.terminate()
            try:
                CURRENT_AUDIO_PROCESS.wait(timeout=1)
            except subprocess.TimeoutExpired:
                CURRENT_AUDIO_PROCESS.kill()
        CURRENT_AUDIO_PROCESS = None

# CAD Logic Imports - CONDITIONAL
if ENABLE_HEAVY:
    from cad.loader import load_step_shape
    from cad.export import export_to_stl
    from cad.tree import build_assembly_tree
    from cad.info import create_cad_summary
    from cad.features import find_cylindrical_faces, create_feature_summary
    from cad.modify import scale_shape, translate_shape, delete_solid, resize_cylindrical_feature, scale_shape_non_uniform, rotate_shape, get_mass_properties
    from ai.cad_command_interpreter import interpret_command, answer_question
    from voice.tts_basic import speak
    import whisper
    WHISPER_MODEL = whisper.load_model("base")
else:
    # Mock functions for demo mode
    def load_step_shape(*args): return None
    def export_to_stl(*args): pass
    def build_assembly_tree(*args): return {"id": "demo", "name": "Demo Mode", "type": "Assembly", "children": []}
    def create_cad_summary(*args): return "Demo mode - CAD features disabled"
    def find_cylindrical_faces(*args): return []
    def create_feature_summary(*args): return "Demo mode"
    def scale_shape(*args): return None
    def translate_shape(*args): return None
    def delete_solid(*args): return None
    def resize_cylindrical_feature(*args): return None
    def scale_shape_non_uniform(*args): return None
    def rotate_shape(*args): return None
    def get_mass_properties(*args): return {}
    def interpret_command(*args): return {"response": "Demo mode - voice features disabled"}
    def answer_question(*args): return "Demo mode"
    def speak(*args): pass
    WHISPER_MODEL = None
from cad.info import create_cad_summary
from cad.features import find_cylindrical_faces, create_feature_summary
from cad.modify import scale_shape, translate_shape, delete_solid, resize_cylindrical_feature, scale_shape_non_uniform, rotate_shape, get_mass_properties
from ai.cad_command_interpreter import interpret_command, answer_question
from voice.tts_basic import speak

app = FastAPI()

# Allow CORS for React Frontend (usually port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Health Check (for Render) --------
@app.get("/")
def health():
    return {
        "status": "ok",
        "heavy_enabled": ENABLE_HEAVY
    }
# -------------------------------------------

# Global State
CURRENT_ASSETS_DIR = "assets"
os.makedirs(CURRENT_ASSETS_DIR, exist_ok=True)
CURRENT_SHAPE = None
CURRENT_STL_PATH = os.path.join(CURRENT_ASSETS_DIR, "model.stl")
WHISPER_MODEL = None

@app.on_event("startup")
def load_models():
    if ENABLE_HEAVY:
        global WHISPER_MODEL
        print("Loading Whisper Model...")
        WHISPER_MODEL = whisper.load_model("small")
        print("Whisper Ready.")
    else:
        print("Demo mode - heavy features disabled")

@app.get("/")
def health():
    return {
        "status": "ok",
        "heavy_enabled": ENABLE_HEAVY
    }

@app.post("/upload")
async def upload_step(file: UploadFile = File(...)):
    if not ENABLE_HEAVY:
        return {
            "status": "disabled",
            "message": "STEP processing disabled on demo server"
        }
    
    global CURRENT_SHAPE
    
    # Save uploaded file
    file_path = os.path.join(CURRENT_ASSETS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        print(f"Loading {file_path}...")
        CURRENT_SHAPE = load_step_shape(file_path)
        
        # Export to STL for Frontend
        export_to_stl(CURRENT_SHAPE, CURRENT_STL_PATH)
        
        # Build Tree
        tree = build_assembly_tree(CURRENT_SHAPE, file_path)
        print(f"Built tree: {tree}")
        
        return {
            "status": "success", 
            "message": "File loaded",
            "tree": tree
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/model.stl")
def get_model():
    if os.path.exists(CURRENT_STL_PATH):
        return FileResponse(CURRENT_STL_PATH)
    return {"error": "No model loaded"}

@app.get("/api/component/{component_id}")
def get_component(component_id: str):
    """Get STL for a specific component"""
    if not CURRENT_SHAPE:
        return {"error": "No model loaded"}
    
    # Create component STL path
    component_stl_path = os.path.join(CURRENT_ASSETS_DIR, f"component_{component_id}.stl")
    
    # Export the specific component
    from cad.export import export_component_to_stl
    result = export_component_to_stl(component_id, component_stl_path)
    
    if result and os.path.exists(component_stl_path):
        return FileResponse(component_stl_path)
    
    return {"error": "Component not found"}

@app.post("/api/voice")
async def process_voice(file: UploadFile = File(...)):
    if not ENABLE_HEAVY:
        return {
            "status": "disabled",
            "message": "Voice disabled on demo server"
        }
    
    global CURRENT_SHAPE, WHISPER_MODEL
    
    if CURRENT_SHAPE is None:
        return {"status": "error", "message": "No model loaded."}

    # Initialize variables to avoid UnboundLocalError
    user_text = ""
    response_text = ""
    modified = False
    tree = None
    cmd_data = {}

    try:
            # 1. Save Audio
        audio_path = os.path.join(CURRENT_ASSETS_DIR, "voice_cmd.wav")
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Stop previous speech immediately when new input is detected
        stop_speaking()
    
        # 2. Transcribe
        result = WHISPER_MODEL.transcribe(
            audio_path, 
            language="en", 
            initial_prompt="CAD design, engineering, 3D modeling, scale, rotate, extrude, feature, radius, diameter"
        )
        user_text = result["text"].strip()
        print(f"User said: {user_text}")
        
        # 2.5 Echo Cancellation
        if LAST_SPOKEN_TEXT:
            similarity = difflib.SequenceMatcher(None, user_text.lower(), LAST_SPOKEN_TEXT.lower()).ratio()
            if similarity > 0.8: # Threshold for echo
                print(f"Ignored Echo (Sim: {similarity:.2f})")
                return {
                    "status": "ignored",
                    "transcription": user_text,
                    "response": "Ignored (Echo)",
                    "modified": False,
                    "tree": None
                }
    
        # 3. Interpret Command
        cmd_data = interpret_command(user_text)
        command = cmd_data.get("command", "UNKNOWN")
        print(f"Command: {command}")
        
        response_text = ""
        modified = False
        
        # 4. Generate Summary for Context (if needed for Q&A)
        # We generate "on demand" or simple cache? Let's regen for now.
        basic_sum = create_cad_summary(CURRENT_SHAPE)
        feat_sum = create_feature_summary(CURRENT_SHAPE)
        full_summary = basic_sum + "\n\nFEATURES:\n" + feat_sum
        
        try:
            if command == "SCALE":
                factor = cmd_data.get("factor", 1.0)
                CURRENT_SHAPE = scale_shape(CURRENT_SHAPE, factor)
                modified = True
                response_text = f"I've scaled the model by a factor of {factor}."
                
            elif command == "MOVE":
                dx = cmd_data.get("dx", 0.0)
                dy = cmd_data.get("dy", 0.0)
                dz = cmd_data.get("dz", 0.0)
                CURRENT_SHAPE = translate_shape(CURRENT_SHAPE, dx, dy, dz)
                modified = True
                response_text = f"I've moved the model by ({dx}, {dy}, {dz})."
                
            elif command == "DELETE":
                idx = cmd_data.get("index", -1)
                CURRENT_SHAPE = delete_solid(CURRENT_SHAPE, idx)
                modified = True
                response_text = "I've removed that part for you."
                
            elif command == "RESIZE_FEATURE":
                 # Simplified Logic from main.py
                 ftype = cmd_data.get("feature_type", "hole")
                 idx = cmd_data.get("index", 0)
                 cyls = find_cylindrical_faces(CURRENT_SHAPE)
                 
                 if not cyls:
                     response_text = f"No {ftype}s found."
                 else:
                     if idx >= len(cyls): idx = 0
                     target = cyls[idx]['face']
                     
                     if "new_radius" in cmd_data:
                         CURRENT_SHAPE = resize_cylindrical_feature(CURRENT_SHAPE, target, cmd_data["new_radius"])
                         response_text = f"Resized {ftype} to radius {cmd_data['new_radius']}."
                         modified = True
                     elif "scale" in cmd_data:
                         # recalc logic
                         curr_r = cyls[idx]['radius']
                         new_r = curr_r * cmd_data["scale"]
                         CURRENT_SHAPE = resize_cylindrical_feature(CURRENT_SHAPE, target, new_r)
                         response_text = f"Resized {ftype} by scale {cmd_data['scale']}."
                         modified = True
            
            elif command == "ROTATE":
                axis = cmd_data.get("axis", "Z")
                angle = cmd_data.get("angle_degrees", 90)
                CURRENT_SHAPE = rotate_shape(CURRENT_SHAPE, axis, angle)
                modified = True
                response_text = f"Done. I've rotated the model {angle} degrees around the {axis} axis."
                
            elif command == "SCALE_NON_UNIFORM":
                # Check if it's axis specific scaling or direct xyz
                if "axis" in cmd_data:
                    axis = cmd_data["axis"].upper()
                    val = cmd_data.get("axis_factor", 1.0)
                    fx, fy, fz = 1.0, 1.0, 1.0
                    if axis == "X": fx = val
                    elif axis == "Y": fy = val
                    elif axis == "Z": fz = val
                    CURRENT_SHAPE = scale_shape_non_uniform(CURRENT_SHAPE, fx, fy, fz)
                    response_text = f"Scaled {axis} axis by {val}."
                else:
                    fx = cmd_data.get("factor_x", 1.0)
                    fy = cmd_data.get("factor_y", 1.0)
                    fz = cmd_data.get("factor_z", 1.0)
                    CURRENT_SHAPE = scale_shape_non_uniform(CURRENT_SHAPE, fx, fy, fz)
                    response_text = f"Scaled non-uniformly ({fx}, {fy}, {fz})."
                modified = True
                
            elif command == "GET_MASS_PROPS":
                props = get_mass_properties(CURRENT_SHAPE)
                vol = props["volume"]
                area = props["area"]
                response_text = f"The model's volume is {vol:.2f} cubic units, and the surface area is {area:.2f} square units."
                
            elif command == "COLOR":
                 # This requires frontend support (metadata per ID).
                 # For now, we can't change color of STEP geometry directly in backend without Metadata wrapper.
                 # We will just respond.
                 col = cmd_data.get("color", "requested color")
                 response_text = f"Color change to {col} is simpler in the UI, but I've noted it."
                 # Logic to actually inject color into GLTF/STL export would be needed here.
            
            elif command == "QUESTION" or command == "UNKNOWN":
                response_text = answer_question(full_summary, user_text)

            elif command == "UNSURE":
                 response_text = "I didn't quite catch that. Could you please say it again?"
                
        except Exception as e:
            print(f"Logic Error: {e}")
            response_text = f"Error: {str(e)}"
            
    except Exception as e:
        print(f"Server Error: {e}")
        response_text = f"System Error: {str(e)}"
        # Ensure user_text is not empty if it failed before transcription
        if not user_text: user_text = "(Audio Processing Failed)"

    # 5. Re-export if modified
    tree = None
    if modified:
        export_to_stl(CURRENT_SHAPE, CURRENT_STL_PATH)
        tree = build_assembly_tree(CURRENT_SHAPE)

    # 6. Speak Response (Async Subprocess)
    if response_text:
        LAST_SPOKEN_TEXT = response_text
        try:
            # Generate file
            audio_file = speak(response_text)
            if audio_file:
                 # Spawn player
                 CURRENT_AUDIO_PROCESS = subprocess.Popen([sys.executable, "voice/player.py", audio_file])
        except Exception as e:
            print(f"TTS Error: {e}")
        
    return {
        "status": "success",
        "transcription": user_text,
        "response": response_text,
        "modified": modified,
        "tree": tree
    }

@app.get("/api/hasse")
def get_hasse_diagram():
    global CURRENT_SHAPE
    from cad.hasse import generate_hasse_data
    
    if CURRENT_SHAPE is None:
        # Return empty structure or dummy
        return {
            "nodes": [{"id": "nodata", "data": {"label": "No Model Loaded"}, "position": {"x": 0, "y": 0}}], 
            "edges": []
        }
    else:
        # Build graph from assembly tree
        # Re-build tree to ensure fresh data
        tree_json = build_assembly_tree(CURRENT_SHAPE)
        data = generate_hasse_data(tree_json)
        return data
