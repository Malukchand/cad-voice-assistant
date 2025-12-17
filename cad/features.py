# cad/features.py
# Basic feature detection + simple 3D viewer for the CAD Voice Assistant.

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import topods  # helper for downcasting
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Cylinder

from OCC.Display.SimpleGui import init_display

# ---- GLOBAL VIEWER OBJECTS ----
_display = None
_start_display = None


def setup_viewer():
    """
    Create the OCC viewer window (only once) and return display + start_display.
    """
    global _display, _start_display
    if _display is None:
        _display, _start_display, add_menu, add_func = init_display()
    return _display, _start_display


def show_shape(shape):
    """
    Show or update the given shape in the 3D viewer window.
    """
    display, _ = setup_viewer()
    display.EraseAll()
    display.DisplayShape(shape, update=True)
    display.FitAll()


def start_viewer_loop():
    """
    Start the GUI loop for the 3D viewer.
    Call this in a separate thread so main thread can run voice loop.
    """
    _, start_display = setup_viewer()
    start_display()


# =======================
# FEATURE DETECTION PART
# =======================

def list_all_faces(shape):
    """
    Return a list of all faces in the shape.
    """
    faces = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        # Downcast to Face using topods helper
        face = topods.Face(explorer.Current())
        faces.append(face)
        explorer.Next()
    return faces


def find_cylindrical_faces(shape):
    """
    Find all cylindrical faces (often holes/bosses).
    Returns list of dicts with radius + axis direction.
    """
    cylinders = []
    faces = list_all_faces(shape)

    for face in faces:
        adaptor = BRepAdaptor_Surface(face, True)
        surf_type = adaptor.GetType()

        if surf_type == GeomAbs_Cylinder:
            cyl = adaptor.Cylinder()
            radius = cyl.Radius()
            axis = cyl.Axis()
            direction = axis.Direction()
            dx, dy, dz = direction.X(), direction.Y(), direction.Z()

            cylinders.append({
                "face": face,
                "radius": radius,
                "axis_dir": (dx, dy, dz),
            })

    return cylinders

def create_feature_summary(shape):
    faces = list_all_faces(shape)
    cylinders = find_cylindrical_faces(shape)

    summary = []
    summary.append(f"Total faces: {len(faces)}")
    summary.append(f"Cylindrical faces (possible holes/bosses): {len(cylinders)}")

    for i, cyl in enumerate(cylinders):
        r = cyl['radius']
        ax = cyl['axis_dir']
        summary.append(f"Cylinder {i+1}: radius = {r:.2f}, axis direction = {ax}")

    return "\n".join(summary)
