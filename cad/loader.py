# cad/loader.py
# Basic STEP file loader using pythonOCC

import os
import uuid

from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopAbs import TopAbs_SOLID
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add

def load_step_shape(filename: str):
    """
    Load a STEP file and return the main shape.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"STEP file not found: {filename}")

    reader = STEPControl_Reader()
    status = reader.ReadFile(filename)

    if status != IFSelect_RetDone:
        raise RuntimeError(f"Error reading STEP file: {filename}")

    # Transfer all roots to internal structures
    ok = reader.TransferRoots()
    if ok == 0:
        raise RuntimeError(f"Error: no geometry could be transferred from {filename}")

    # Get the combined shape
    shape = reader.OneShape()
    print(f"Loaded STEP file with {count_solids(shape)} solids")
    return shape


def count_solids(shape):
    """
    Count how many SOLID bodies are in the shape.
    """
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    count = 0
    while explorer.More():
        count += 1
        explorer.Next()
    return count


def get_bounding_box(shape):
    """
    Get the bounding box of the shape.
    Returns: xmin, ymin, zmin, xmax, ymax, zmax, dx, dy, dz
    """
    bbox = Bnd_Box()
    brepbndlib_Add(shape, bbox)
    
    if bbox.IsVoid():
        return 0, 0, 0, 0, 0, 0, 0, 0, 0
    
    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dx = xmax - xmin
    dy = ymax - ymin
    dz = zmax - zmin
    
    return xmin, ymin, zmin, xmax, ymax, zmax, dx, dy, dz


def parse_step_assembly(filename: str):
    """
    Parse STEP file to extract assembly structure.
    Returns a dict with the tree structure.
    """
    import re
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except (FileNotFoundError, IOError):
        return None
    
    # Parse PRODUCT entities for names
    products = {}
    product_pattern = r'#(\d+)\s*=\s*PRODUCT\s*\(\s*\'([^\']*)\''
    for match in re.finditer(product_pattern, content):
        id_num = match.group(1)
        name = match.group(2)
        products[id_num] = {'name': name, 'children': []}
    
    # Parse NEXT_ASSEMBLY_USAGE_OCCURRENCE for assembly relationships
    assembly_pattern = r'#(\d+)\s*=\s*NEXT_ASSEMBLY_USAGE_OCCURRENCE\(\s*\'[^\']*\'\s*,\s*[^,]*,\s*#(\d+)\s*,\s*#(\d+)'
    for match in re.finditer(assembly_pattern, content):
        parent_id = match.group(2)
        child_id = match.group(3)
        if parent_id in products and child_id in products:
            products[parent_id]['children'].append(child_id)
    
    if products:
        # Find root (product not used as child)
        all_children = set()
        for prod in products.values():
            all_children.update(prod['children'])
        
        root_id = None
        for id_num, prod in products.items():
            if id_num not in all_children:
                root_id = id_num
                break
        
        if not root_id:
            # If no clear root, use the first product
            root_id = list(products.keys())[0]
        
        def build_tree(node_id):
            if node_id not in products:
                return {'id': str(uuid.uuid4()), 'name': f'Unknown {node_id}', 'type': 'Part', 'children': []}
            
            prod = products[node_id]
            children = [build_tree(child_id) for child_id in prod['children']]
            
            # Determine type: if has children, Assembly, else Part
            node_type = 'Assembly' if children else 'Part'
            
            return {
                'id': str(uuid.uuid4()),
                'name': prod['name'] or f'Component {node_id}',
                'type': node_type,
                'children': children
            }
        
        tree = build_tree(root_id)
        print(f"Parsed STEP assembly tree with {len(products)} products")
        return tree
    
    # If no products found, return None to trigger fallback
    return None
