"""
Procedural 3D Material Pack Generator — v2 (EEVEE, robust)
Blender 5.2 headless
Run: blender --background --python generate_assets.py
"""
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore')

import bpy
import os
import math
import traceback

# ─── Config ───────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

RES = 512
SAMPLES = 64

# ─── Scene Setup ──────────────────────────────────────────────────────────
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = False
    # EEVEE (confirmed working in 5.2)
    scene.render.engine = 'BLENDER_EEVEE'
    try:
        scene.eevee.taa_render_samples = SAMPLES
    except AttributeError:
        pass
    try:
        scene.eevee.use_gtao = True
    except AttributeError:
        pass
    try:
        scene.eevee.gtao_distance = 1.0
    except AttributeError:
        pass
    try:
        scene.eevee.use_bloom = False
    except AttributeError:
        pass
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium Contrast'
    return scene

def setup_lighting(scene):
    # Key
    kd = bpy.data.lights.new("Key", type='AREA')
    kd.energy = 150
    kd.size = 3
    ko = bpy.data.objects.new("Key", kd)
    bpy.context.collection.objects.link(ko)
    ko.location = (2.5, 2, 4)
    ko.rotation_euler = (math.radians(45), math.radians(10), math.radians(-20))

    # Fill
    fd = bpy.data.lights.new("Fill", type='AREA')
    fd.energy = 50
    fd.size = 5
    fo = bpy.data.objects.new("Fill", fd)
    bpy.context.collection.objects.link(fo)
    fo.location = (-2.5, 3, 3)
    fo.rotation_euler = (math.radians(55), math.radians(-10), math.radians(20))

    # Rim
    rd = bpy.data.lights.new("Rim", type='AREA')
    rd.energy = 60
    rd.size = 2
    ro = bpy.data.objects.new("Rim", rd)
    bpy.context.collection.objects.link(ro)
    ro.location = (0, -3.5, 3.5)
    ro.rotation_euler = (math.radians(70), 0, 0)

    # Camera
    cd = bpy.data.cameras.new("Camera")
    cd.lens = 50
    co = bpy.data.objects.new("Camera", cd)
    bpy.context.collection.objects.link(co)
    co.location = (0, -3.2, 2.0)
    co.rotation_euler = (math.radians(60), 0, 0)
    scene.camera = co

    # World
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.04, 0.04, 0.06, 1)
        bg.inputs['Strength'].default_value = 0.4

def create_test_mesh():
    bpy.ops.mesh.primitive_cylinder_add(radius=1.3, depth=0.3, location=(0, 0, 0.15), vertices=48)
    cyl = bpy.context.active_object
    cyl.name = "Cyl"
    bev = cyl.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.025
    bev.segments = 3
    bpy.ops.object.shade_smooth()

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.55, location=(0.85, 0.45, 0.55), segments=32, ring_count=24)
    sph = bpy.context.active_object
    sph.name = "Sph"
    bpy.ops.object.shade_smooth()
    return [cyl, sph]

def clear_meshes():
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)

# ─── Material Helpers ─────────────────────────────────────────────────────
def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nd = mat.node_tree.nodes
    ln = mat.node_tree.links
    for n in list(nd):
        nd.remove(n)
    return mat, nd, ln

def _add_out(nd, ln, bsdf):
    out = nd.new('ShaderNodeOutputMaterial')
    out.location = (700, 0)
    ln.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

def _pr(nd, rough=0.5, metal=0.0):
    b = nd.new('ShaderNodeBsdfPrincipled')
    b.location = (400, 0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return b

# ─── 12 Materials ─────────────────────────────────────────────────────────
def mat_wood_oak():
    m, nd, ln = _new_mat("Wood_Oak")
    b = _pr(nd, 0.55)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    mp = nd.new('ShaderNodeMapping'); mp.location = (-600, 0)
    mp.inputs['Scale'].default_value = (1, 12, 1)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-400, 0)
    nz.inputs['Scale'].default_value = 4; nz.inputs['Detail'].default_value = 6
    wv = nd.new('ShaderNodeTexWave'); wv.location = (-200, 0)
    wv.inputs['Scale'].default_value = 1.5; wv.inputs['Distortion'].default_value = 6
    wv.inputs['Detail'].default_value = 4; wv.bands_direction = 'Y'
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.12, 0.06, 0.02, 1)
    rp.color_ramp.elements[1].color = (0.42, 0.24, 0.09, 1)
    ln.new(tc.outputs['Object'], mp.inputs['Vector'])
    ln.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ln.new(mp.outputs['Vector'], wv.inputs['Vector'])
    ln.new(nz.outputs['Fac'], wv.inputs['Distortion'])
    ln.new(wv.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_wood_walnut():
    m, nd, ln = _new_mat("Wood_Walnut")
    b = _pr(nd, 0.5)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    mp = nd.new('ShaderNodeMapping'); mp.location = (-600, 0)
    mp.inputs['Scale'].default_value = (0.8, 10, 0.8)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-400, 0)
    nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 8
    wv = nd.new('ShaderNodeTexWave'); wv.location = (-200, 0)
    wv.inputs['Scale'].default_value = 2; wv.inputs['Distortion'].default_value = 4
    wv.inputs['Detail'].default_value = 5; wv.bands_direction = 'Y'
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.08, 0.04, 0.02, 1)
    rp.color_ramp.elements[1].color = (0.28, 0.14, 0.06, 1)
    ln.new(tc.outputs['Object'], mp.inputs['Vector'])
    ln.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ln.new(mp.outputs['Vector'], wv.inputs['Vector'])
    ln.new(nz.outputs['Fac'], wv.inputs['Distortion'])
    ln.new(wv.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_brushed_steel():
    m, nd, ln = _new_mat("Brushed_Steel")
    b = _pr(nd, 0.25, 1.0)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    mp = nd.new('ShaderNodeMapping'); mp.location = (-600, 0)
    mp.inputs['Scale'].default_value = (1, 80, 1)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-400, 0)
    nz.inputs['Scale'].default_value = 2; nz.inputs['Detail'].default_value = 10
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.55, 0.56, 0.58, 1)
    rp.color_ramp.elements[1].color = (0.75, 0.76, 0.78, 1)
    ln.new(tc.outputs['Object'], mp.inputs['Vector'])
    ln.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ln.new(nz.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    ln.new(nz.outputs['Fac'], b.inputs['Roughness'])
    _add_out(nd, ln, b)
    return m

def mat_copper():
    m, nd, ln = _new_mat("Copper")
    b = _pr(nd, 0.2, 1.0)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-500, 0)
    nz.inputs['Scale'].default_value = 15; nz.inputs['Detail'].default_value = 6
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.72, 0.32, 0.18, 1)
    rp.color_ramp.elements[1].color = (0.85, 0.45, 0.25, 1)
    ln.new(tc.outputs['Object'], nz.inputs['Vector'])
    ln.new(nz.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_concrete():
    m, nd, ln = _new_mat("Concrete")
    b = _pr(nd, 0.85)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    nz1 = nd.new('ShaderNodeTexNoise'); nz1.location = (-500, 100)
    nz1.inputs['Scale'].default_value = 8; nz1.inputs['Detail'].default_value = 12
    nz2 = nd.new('ShaderNodeTexNoise'); nz2.location = (-500, -100)
    nz2.inputs['Scale'].default_value = 30; nz2.inputs['Detail'].default_value = 8
    mix = nd.new('ShaderNodeMix'); mix.location = (-200, 0)
    mix.data_type = 'FLOAT'; mix.inputs['Factor'].default_value = 0.4
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.35, 0.35, 0.33, 1)
    rp.color_ramp.elements[1].color = (0.55, 0.54, 0.52, 1)
    ln.new(tc.outputs['Object'], nz1.inputs['Vector'])
    ln.new(tc.outputs['Object'], nz2.inputs['Vector'])
    ln.new(nz1.outputs['Fac'], mix.inputs['A'])
    ln.new(nz2.outputs['Fac'], mix.inputs['B'])
    ln.new(mix.outputs['Result'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    ln.new(nz2.outputs['Fac'], b.inputs['Roughness'])
    _add_out(nd, ln, b)
    return m

def mat_marble():
    m, nd, ln = _new_mat("Marble_White")
    b = _pr(nd, 0.15)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    mp = nd.new('ShaderNodeMapping'); mp.location = (-600, 0)
    mp.inputs['Scale'].default_value = (2, 2, 2)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-400, 0)
    nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 8
    wv = nd.new('ShaderNodeTexWave'); wv.location = (-200, 0)
    wv.inputs['Scale'].default_value = 3; wv.inputs['Distortion'].default_value = 8
    wv.inputs['Detail'].default_value = 3; wv.wave_profile = 'TRI'
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.05, 0.05, 0.06, 1)
    rp.color_ramp.elements[1].color = (0.92, 0.92, 0.90, 1)
    ln.new(tc.outputs['Object'], mp.inputs['Vector'])
    ln.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ln.new(mp.outputs['Vector'], wv.inputs['Vector'])
    ln.new(nz.outputs['Fac'], wv.inputs['Distortion'])
    ln.new(wv.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_granite():
    m, nd, ln = _new_mat("Granite_Gray")
    b = _pr(nd, 0.7)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    vor = nd.new('ShaderNodeTexVoronoi'); vor.location = (-400, 0)
    vor.inputs['Scale'].default_value = 25; vor.feature = 'F1'
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-400, -200)
    nz.inputs['Scale'].default_value = 50; nz.inputs['Detail'].default_value = 4
    mix = nd.new('ShaderNodeMix'); mix.location = (-100, 0)
    mix.data_type = 'RGBA'; mix.inputs['Factor'].default_value = 0.3
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.2, 0.2, 0.22, 1)
    rp.color_ramp.elements[1].color = (0.5, 0.5, 0.52, 1)
    ln.new(tc.outputs['Object'], vor.inputs['Vector'])
    ln.new(tc.outputs['Object'], nz.inputs['Vector'])
    ln.new(vor.outputs['Distance'], mix.inputs['A'])
    ln.new(nz.outputs['Fac'], mix.inputs['B'])
    ln.new(mix.outputs['Result'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_leather():
    m, nd, ln = _new_mat("Leather_Brown")
    b = _pr(nd, 0.75)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    vor = nd.new('ShaderNodeTexVoronoi'); vor.location = (-500, 0)
    vor.inputs['Scale'].default_value = 30; vor.feature = 'F1'
    try:
        vor.distance_metric = 'MINKOVSKY'
    except AttributeError:
        pass
    try:
        vor.inputs['Exponent'].default_value = 3
    except (AttributeError, KeyError):
        pass
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-500, -200)
    nz.inputs['Scale'].default_value = 8; nz.inputs['Detail'].default_value = 10
    mix = nd.new('ShaderNodeMix'); mix.location = (-200, 0)
    mix.data_type = 'FLOAT'; mix.inputs['Factor'].default_value = 0.5
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.15, 0.06, 0.02, 1)
    rp.color_ramp.elements[1].color = (0.35, 0.15, 0.05, 1)
    ln.new(tc.outputs['Object'], vor.inputs['Vector'])
    ln.new(tc.outputs['Object'], nz.inputs['Vector'])
    ln.new(vor.outputs['Distance'], mix.inputs['A'])
    ln.new(nz.outputs['Fac'], mix.inputs['B'])
    ln.new(mix.outputs['Result'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_fabric():
    m, nd, ln = _new_mat("Fabric_Weave_Red")
    b = _pr(nd, 0.9)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    ck1 = nd.new('ShaderNodeTexChecker'); ck1.location = (-500, 100)
    ck1.inputs['Scale'].default_value = 40
    ck1.inputs['Color1'].default_value = (0.6, 0.1, 0.1, 1)
    ck1.inputs['Color2'].default_value = (0.45, 0.08, 0.08, 1)
    ck2 = nd.new('ShaderNodeTexChecker'); ck2.location = (-500, -100)
    ck2.inputs['Scale'].default_value = 40
    ck2.inputs['Color1'].default_value = (0.5, 0.09, 0.09, 1)
    ck2.inputs['Color2'].default_value = (0.65, 0.12, 0.1, 1)
    rot = nd.new('ShaderNodeMapping'); rot.location = (-650, -100)
    rot.inputs['Rotation'].default_value = (0, 0, math.radians(90))
    mix = nd.new('ShaderNodeMix'); mix.location = (-200, 0)
    mix.data_type = 'RGBA'; mix.inputs['Factor'].default_value = 0.5
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-200, -200)
    nz.inputs['Scale'].default_value = 100; nz.inputs['Detail'].default_value = 3
    ln.new(tc.outputs['Object'], ck1.inputs['Vector'])
    ln.new(tc.outputs['Object'], rot.inputs['Vector'])
    ln.new(rot.outputs['Vector'], ck2.inputs['Vector'])
    ln.new(ck1.outputs['Color'], mix.inputs['A'])
    ln.new(ck2.outputs['Color'], mix.inputs['B'])
    ln.new(tc.outputs['Object'], nz.inputs['Vector'])
    ln.new(mix.outputs['Result'], b.inputs['Base Color'])
    ln.new(nz.outputs['Fac'], b.inputs['Roughness'])
    _add_out(nd, ln, b)
    return m

def mat_glass():
    m, nd, ln = _new_mat("Glass_Clear")
    b = _pr(nd, 0.02)
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.5
    b.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1)
    _add_out(nd, ln, b)
    return m

def mat_gold():
    m, nd, ln = _new_mat("Gold_Polished")
    b = _pr(nd, 0.1, 1.0)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-500, 0)
    nz.inputs['Scale'].default_value = 5; nz.inputs['Detail'].default_value = 4
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.85, 0.65, 0.13, 1)
    rp.color_ramp.elements[1].color = (1.0, 0.82, 0.25, 1)
    ln.new(tc.outputs['Object'], nz.inputs['Vector'])
    ln.new(nz.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

def mat_bark():
    m, nd, ln = _new_mat("Bark_Oak")
    b = _pr(nd, 0.9)
    tc = nd.new('ShaderNodeTexCoord'); tc.location = (-800, 0)
    mp = nd.new('ShaderNodeMapping'); mp.location = (-650, 0)
    mp.inputs['Scale'].default_value = (1, 6, 1)
    nz = nd.new('ShaderNodeTexNoise'); nz.location = (-450, 100)
    nz.inputs['Scale'].default_value = 5; nz.inputs['Detail'].default_value = 14
    wv = nd.new('ShaderNodeTexWave'); wv.location = (-250, 0)
    wv.inputs['Scale'].default_value = 3; wv.inputs['Distortion'].default_value = 10
    wv.inputs['Detail'].default_value = 6; wv.bands_direction = 'Y'
    rp = nd.new('ShaderNodeValToRGB'); rp.location = (100, -100)
    rp.color_ramp.elements[0].color = (0.06, 0.03, 0.01, 1)
    rp.color_ramp.elements[1].color = (0.25, 0.15, 0.06, 1)
    ln.new(tc.outputs['Object'], mp.inputs['Vector'])
    ln.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ln.new(mp.outputs['Vector'], wv.inputs['Vector'])
    ln.new(nz.outputs['Fac'], wv.inputs['Distortion'])
    ln.new(wv.outputs['Fac'], rp.inputs['Fac'])
    ln.new(rp.outputs['Color'], b.inputs['Base Color'])
    _add_out(nd, ln, b)
    return m

# ─── Pipeline ─────────────────────────────────────────────────────────────
MATERIALS = [
    ("wood_oak", mat_wood_oak),
    ("wood_walnut", mat_wood_walnut),
    ("brushed_steel", mat_brushed_steel),
    ("copper", mat_copper),
    ("concrete", mat_concrete),
    ("marble_white", mat_marble),
    ("granite_gray", mat_granite),
    ("leather_brown", mat_leather),
    ("fabric_weave_red", mat_fabric),
    ("glass_clear", mat_glass),
    ("gold_polished", mat_gold),
    ("bark_oak", mat_bark),
]

def generate_all():
    print("=" * 55)
    print("MATERIAL PACK v2 — EEVEE, 512px, 64spp")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 55)

    scene = reset_scene()
    setup_lighting(scene)

    ok, fail = 0, 0
    manifest = []

    for idx, (name, builder) in enumerate(MATERIALS, 1):
        print(f"\n[{idx:2d}/12] {name}", flush=True)
        try:
            clear_meshes()
            mat = builder()
            meshes = create_test_mesh()
            for mo in meshes:
                mo.data.materials.clear()
                mo.data.materials.append(mat)

            png = os.path.join(OUTPUT_DIR, f"preview_{name}.png")
            scene.render.filepath = png
            bpy.ops.render.render(write_still=True)
            print(f"  OK preview → {os.path.basename(png)}", flush=True)

            bl = os.path.join(OUTPUT_DIR, f"{name}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=bl)
            print(f"  OK blend   → {os.path.basename(bl)}", flush=True)

            manifest.append(f"{name}\t{bl}\t{png}")
            ok += 1
        except Exception as e:
            print(f"  FAIL: {e}", flush=True)
            traceback.print_exc()
            fail += 1
            # try to recover scene
            try:
                clear_meshes()
            except Exception:
                pass

    # Manifest
    mp = os.path.join(OUTPUT_DIR, "manifest.txt")
    with open(mp, 'w') as f:
        f.write("name\tblend_file\tpreview_image\n")
        f.write("\n".join(manifest) + "\n")

    print(f"\n{'='*55}")
    print(f"DONE: {ok} ok, {fail} failed, {len(MATERIALS)} total")
    print(f"Manifest: {mp}")
    print(f"{'='*55}")

if __name__ == "__main__":
    generate_all()
