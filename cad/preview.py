# cad/preview.py
# Create a simple 3D preview image from an OCC shape.

import os
import tempfile

from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer

import pyvista as pv


def create_preview_image(shape, image_path: str | None = None) -> str:
    """
    Take an OCC TopoDS_Shape and generate a PNG image path
    showing a simple isometric 3D view.

    Returns the path to the PNG image.
    """

    # 1) Triangulate and export to STL (temporary file)
    if image_path is None:
        tmp_dir = tempfile.gettempdir()
        image_path = os.path.join(tmp_dir, "cad_preview.png")

    stl_path = image_path.replace(".png", ".stl")

    # Mesh the shape for STL export
    # 0.5 is a decent deflection for medium-sized models; adjust if needed.
    BRepMesh_IncrementalMesh(shape, 0.5)

    writer = StlAPI_Writer()
    writer.Write(shape, stl_path)

    # 2) Load STL with PyVista and render off-screen
    mesh = pv.read(stl_path)

    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh, show_edges=True)
    plotter.view_isometric()
    plotter.set_background("white")

    # Save screenshot
    plotter.show(screenshot=image_path)

    return image_path
