# cad/tree.py
# Helper to generate assembly tree JSON structure

from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE
import uuid
from .loader import parse_step_assembly

# Global storage for shape references (component_id -> shape)
SHAPE_REFS = {}

def build_assembly_tree(shape, step_filename=None):
    """
    Build assembly tree. Try to parse STEP file for assembly structure first,
    then show solids under the product.
    """
    
    root_name = "Assembly"
    root_type = "Assembly"
    
    if step_filename:
        parsed_tree = parse_step_assembly(step_filename)
        if parsed_tree:
            # Use parsed product as root
            root_name = parsed_tree['name']
            root_type = parsed_tree['type']
    
    root_id = str(uuid.uuid4())
    tree = {
        "id": root_id,
        "name": root_name,
        "type": root_type,
        "children": []
    }
    
    # Clear previous shape refs
    SHAPE_REFS.clear()
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    solid_index = 1
    while explorer.More():
        solid_shape = explorer.Current()
        solid_id = str(uuid.uuid4())
        solid_name = f"Solid {solid_index}"
        solid_node = {
            "id": solid_id,
            "name": solid_name,
            "type": "Part",
            "children": []
        }
        
        # Store shape reference
        SHAPE_REFS[solid_id] = solid_shape
        
        # Add shells within this solid
        shell_explorer = TopExp_Explorer(solid_shape, TopAbs_SHELL)
        shell_index = 1
        while shell_explorer.More():
            shell_shape = shell_explorer.Current()
            shell_id = str(uuid.uuid4())
            shell_name = f"Shell {shell_index}"
            shell_node = {
                "id": shell_id,
                "name": shell_name,
                "type": "Shell",
                "children": []
            }
            
            # Store shape reference
            SHAPE_REFS[shell_id] = shell_shape
            
            # Add faces within this shell
            face_explorer = TopExp_Explorer(shell_shape, TopAbs_FACE)
            face_index = 1
            while face_explorer.More():
                face_shape = face_explorer.Current()
                face_id = str(uuid.uuid4())
                face_name = f"Face {face_index}"
                face_node = {
                    "id": face_id,
                    "name": face_name,
                    "type": "Face",
                    "children": []
                }
                
                # Store shape reference
                SHAPE_REFS[face_id] = face_shape
                shell_node["children"].append(face_node)
                face_explorer.Next()
                face_index += 1
            
            solid_node["children"].append(shell_node)
            shell_explorer.Next()
            shell_index += 1
        
        tree["children"].append(solid_node)
        explorer.Next()
        solid_index += 1
    
    print(f"Built tree with {len(tree['children'])} solids")
    return tree
