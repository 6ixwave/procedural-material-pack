"""Render ONE material in a fresh Blender process.
Usage: blender --background --python render_one.py <material_name>
"""
import sys, os, warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import bpy
import math
from generate_assets import (
    MATERIALS, reset_scene, setup_lighting,
    create_test_mesh, clear_meshes, OUTPUT_DIR, RES, SAMPLES
)

def main():
    # Extract material name from Blender argv
    args = sys.argv
    try:
        idx = args.index(os.path.basename(__file__))
        extra = args[idx + 1:]
    except ValueError:
        extra = [args[-1]] if len(args) > 1 else []

    name = extra[0] if extra else "wood_oak"

    builder = None
    for n, fn in MATERIALS:
        if n == name:
            builder = fn
            break
    if not builder:
        avail = [n for n, _ in MATERIALS]
        print(f"ERROR: unknown material '{name}'. Available: {avail}", flush=True)
        sys.exit(1)

    print(f"RENDERING: {name}  ({RES}px, {SAMPLES}spp, EEVEE)", flush=True)

    scene = reset_scene()
    setup_lighting(scene)

    mat = builder()
    meshes = create_test_mesh()
    for mo in meshes:
        mo.data.materials.clear()
        mo.data.materials.append(mat)

    png = os.path.join(OUTPUT_DIR, f"preview_{name}.png")
    scene.render.filepath = png
    bpy.ops.render.render(write_still=True)
    print(f"  OK preview -> {os.path.basename(png)}", flush=True)

    bl = os.path.join(OUTPUT_DIR, f"{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=bl)
    print(f"  OK blend   -> {os.path.basename(bl)}", flush=True)

    print(f"DONE: {name}", flush=True)

main()
