# cad/export.py
# Export functions for Web Viewer (STL/GLB)

import os
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

def export_to_stl(shape, filename: str, deflection=0.01):
    """
    Export the shape to an ASCII or Binary STL file.
    Must mesh the shape first.
    """
    # 1. Mesh the shape
    mesh = BRepMesh_IncrementalMesh(shape, deflection)
    
    # 2. Write STL
    writer = StlAPI_Writer()
    writer.Write(shape, filename)
    
    return filename

def export_component_to_stl(component_id: str, filename: str, deflection=0.01):
    """
    Export a specific component to STL by its ID.
    """
    from .tree import SHAPE_REFS
    
    if component_id not in SHAPE_REFS:
        return None
    
    shape = SHAPE_REFS[component_id]
    
    # Mesh and export
    mesh = BRepMesh_IncrementalMesh(shape, deflection)
    writer = StlAPI_Writer()
    writer.Write(shape, filename)
    
    return filename
