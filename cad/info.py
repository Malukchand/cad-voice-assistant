# cad/info.py
# Create a human-readable CAD summary for the AI

from cad.loader import count_solids, get_bounding_box

def create_cad_summary(shape) -> str:
    """
    Convert raw CAD geometry into a human-readable summary.
    The AI will use this context to answer product questions.
    """
    num_solids = count_solids(shape)
    xmin, ymin, zmin, xmax, ymax, zmax, dx, dy, dz = get_bounding_box(shape)

    summary = f"""
CAD Model Summary:
- Number of bodies: {num_solids}
- Bounding box:
    - X range: {xmin:.2f} to {xmax:.2f}   (width = {dx:.2f})
    - Y range: {ymin:.2f} to {ymax:.2f}   (depth = {dy:.2f})
    - Z range: {zmin:.2f} to {zmax:.2f}   (height = {dz:.2f})

Interpretation:
- The model has {num_solids} solid part(s).
- Its overall size is:
    Width = {dx:.2f}
    Depth = {dy:.2f}
    Height = {dz:.2f}
"""
    return summary
