"""Quick test: render ONE material with EEVEE to verify engine works."""
import warnings
warnings.filterwarnings('ignore')
import bpy, os, math, traceback

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)

try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # Engine: try BLENDER_EEVEE first (5.x), fallback to BLENDER_EEVEE_NEXT
    try:
        scene.render.engine = 'BLENDER_EEVEE'
        print("Engine: BLENDER_EEVEE", flush=True)
    except Exception as e:
        print(f"BLENDER_EEVEE failed: {e}, trying BLENDER_EEVEE_NEXT", flush=True)
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        print("Engine: BLENDER_EEVEE_NEXT", flush=True)

    # EEVEE settings (wrap in try for version differences)
    try:
        scene.eevee.taa_render_samples = 32
    except Exception:
        pass
    try:
        scene.eevee.use_gtao = True
    except Exception:
        pass

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium Contrast'

    # Simple light + camera
    ld = bpy.data.lights.new("L", type='AREA')
    ld.energy = 100; ld.size = 3
    lo = bpy.data.objects.new("L", ld)
    bpy.context.collection.objects.link(lo)
    lo.location = (2, 2, 4)
    lo.rotation_euler = (math.radians(45), 0, 0)

    cd = bpy.data.cameras.new("Cam")
    cd.lens = 50
    co = bpy.data.objects.new("Cam", cd)
    bpy.context.collection.objects.link(co)
    co.location = (0, -3, 2)
    co.rotation_euler = (math.radians(60), 0, 0)
    scene.camera = co

    # World
    w = bpy.data.worlds.new("W")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.04, 0.04, 0.06, 1)
        bg.inputs['Strength'].default_value = 0.4

    # Mesh: cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.3, location=(0,0,0.15), vertices=48)
    cyl = bpy.context.active_object
    bpy.ops.object.shade_smooth()

    # Material: simple wood
    mat = bpy.data.materials.new("TestWood")
    mat.use_nodes = True
    nd = mat.node_tree.nodes
    ln = mat.node_tree.links
    for n in list(nd): nd.remove(n)
    out = nd.new('ShaderNodeOutputMaterial'); out.location = (500, 0)
    b = nd.new('ShaderNodeBsdfPrincipled'); b.location = (200, 0)
    b.inputs['Roughness'].default_value = 0.5
    b.inputs['Base Color'].default_value = (0.4, 0.2, 0.08, 1)
    ln.new(b.outputs['BSDF'], out.inputs['Surface'])
    cyl.data.materials.append(mat)

    # Render
    png = os.path.join(OUT, "test_preview.png")
    scene.render.filepath = png
    bpy.ops.render.render(write_still=True)
    print(f"RENDER OK: {png}", flush=True)
    print("TEST PASSED", flush=True)

except Exception as e:
    print(f"TEST FAILED: {e}", flush=True)
    traceback.print_exc()
    raise SystemExit(1)
