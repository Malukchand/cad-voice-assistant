# cad/modify.py
# Basic CAD modification functions: scale, translate, rotate, save, delete

from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop_VolumeProperties, brepgprop_SurfaceProperties
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Ax1, gp_Pnt, gp_Dir, gp_Mat
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound

def scale_shape_non_uniform(shape, fx: float, fy: float, fz: float):
    """
    Non-uniform scaling using gp_Mat.
    Note: OCC gp_Trsf usually supports uniform scale. 
    For non-uniform, we might need GCE2d or specific Displacement.
    Actually, standard gp_Trsf only supports Homothetic (uniform).
    For non-uniform, we need BRepBuilderAPI_NurbsConvert or similar if we want to deform?
    WAIT - gp_GTrsf (General Transformation) supports non-uniform scaling.
    """
    from OCC.Core.gp import gp_GTrsf, gp_Mat
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_GTransform

    mat = gp_Mat(fx, 0, 0, 
                 0, fy, 0, 
                 0, 0, fz)
    
    if abs(fx) < 1e-9 or abs(fy) < 1e-9 or abs(fz) < 1e-9:
        raise ValueError("Scale factors must be non-zero.")

    gtrsf = gp_GTrsf(mat, gp_Vec(0,0,0))
    
    # GTransform is required for non-uniform (affinity)
    transformer = BRepBuilderAPI_GTransform(shape, gtrsf, True) 
    return transformer.Shape()


def rotate_shape(shape, axis_char: str, angle_degrees: float):
    """
    Rotate shape around global X, Y, or Z axis.
    """
    import math
    rad = math.radians(angle_degrees)
    
    axis_dir = gp_Dir(0,0,1) # Default Z
    if axis_char.upper() == "X": axis_dir = gp_Dir(1,0,0)
    elif axis_char.upper() == "Y": axis_dir = gp_Dir(0,1,0)
    
    ax1 = gp_Ax1(gp_Pnt(0,0,0), axis_dir)
    
    trsf = gp_Trsf()
    trsf.SetRotation(ax1, rad)
    
    transformer = BRepBuilderAPI_Transform(shape, trsf, True)
    return transformer.Shape()

def get_mass_properties(shape):
    """
    Calculate volume and surface area.
    """
    gprops = GProp_GProps()
    brepgprop_VolumeProperties(shape, gprops)
    vol = gprops.Mass()
    
    brepgprop_SurfaceProperties(shape, gprops)
    area = gprops.Mass() # For surface props, Mass is Area
    
    return {"volume": vol, "area": area}

def scale_shape(shape, scale_factor: float):
    """
    Uniformly scale the entire shape around the origin.
    """
    if abs(scale_factor) < 1e-9:
        raise ValueError("Scale factor must be non-zero.")
        
    trsf = gp_Trsf()
    trsf.SetScale(gp_Pnt(0,0,0), scale_factor)
    transformer = BRepBuilderAPI_Transform(shape, trsf, True)
    return transformer.Shape()


def translate_shape(shape, dx: float, dy: float, dz: float):
    """
    Translate (move) the shape by dx, dy, dz.
    """
    vec = gp_Vec(dx, dy, dz)
    trsf = gp_Trsf()
    trsf.SetTranslation(vec)
    transformer = BRepBuilderAPI_Transform(shape, trsf, True)
    return transformer.Shape()


def save_step(shape, filename: str):
    """
    Save a shape to a STEP file.
    """
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    status = writer.Write(filename)

    if status != IFSelect_RetDone:
        raise RuntimeError(f"Error writing STEP file: {filename}")

def resize_cylindrical_feature(shape, face, new_radius):
    """
    Resize a cylindrical surface (hole/boss) to a new radius.
    Uses radial scaling around the cylinder axis.
    """
    from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
    adaptor = BRepAdaptor_Surface(face, True)
    cyl = adaptor.Cylinder()

    old_radius = cyl.Radius()
    axis = cyl.Axis()

    # Compute scale factor
    if old_radius < 1e-6:
        return shape # Avoid division by zero
    factor = new_radius / old_radius

    # Create transformation:
    # scale around cylinder axis (gp_Ax1)
    trsf = gp_Trsf()
    trsf.SetScale(axis, factor)  # scale around axis

    transformer = BRepBuilderAPI_Transform(shape, trsf, True)
    modified_shape = transformer.Shape()

    return modified_shape

def delete_solid(shape, index: int):
    """
    Remove a specific solid from the compound shape.
    If index is out of bounds or -1, might delete all or specific one.
    Here we implement:
      - split into solids
      - keep all except the one at 'index'
    """
    solids = []
    exp = TopExp_Explorer(shape, TopAbs_SOLID)
    while exp.More():
        solids.append(topods.Solid(exp.Current()))
        exp.Next()

    if not solids:
        # It might be a single solid itself
        if shape.ShapeType() == TopAbs_SOLID:
             solids = [topods.Solid(shape)]
        else:
             return shape # Nothing to delete

    if index < 0 or index >= len(solids):
        # If user says "delete part" but we have 5 parts, maybe delete the LAST one?
        # Or if index is -1, maybe delete the largest?
        # For safety/simplicity, if index is invalid (-1), let's delete the FIRST one (index 0).
        to_delete = 0
    else:
        to_delete = index

    # Rebuild compound without the deleted solid
    builder = BRep_Builder()
    comp = TopoDS_Compound()
    builder.MakeCompound(comp)
    
    count = 0
    for i, s in enumerate(solids):
        if i == to_delete:
            continue
        builder.Add(comp, s)
        count += 1
    
    if count == 0:
        # We deleted the only solid? Return empty compound?
        # Or creating an empty compound might crash viewer.
        # Let's return the empty compound and hope viewer handles it.
        pass

    return comp
