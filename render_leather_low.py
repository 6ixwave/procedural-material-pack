"""Render leather_brown with reduced GPU load to dodge atio6axx.dll crash."""
import sys, os, warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import bpy
import math

OUT = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUT, exist_ok=True)

# --- Scene ---
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.engine = 'BLENDER_EEVEE'
try:
    scene.eevee.taa_render_samples = 16  # reduced from 64
except AttributeError:
    pass
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium Contrast'

# --- Lighting (simpler: 2 lights instead of 3) ---
ld = bpy.data.lights.new("Key", type='AREA')
ld.energy = 120; ld.size = 3
lo = bpy.data.objects.new("Key", ld)
bpy.context.collection.objects.link(lo)
lo.location = (2, 2, 4)
lo.rotation_euler = (math.radians(45), 0, 0)

fd = bpy.data.lights.new("Fill", type='AREA')
fd.energy = 40; fd.size = 4
fo = bpy.data.objects.new("Fill", fd)
bpy.context.collection.objects.link(fo)
fo.location = (-2, 3, 3)
fo.rotation_euler = (math.radians(55), 0, 0)

cd = bpy.data.cameras.new("Cam")
cd.lens = 50
co = bpy.data.objects.new("Cam", cd)
bpy.context.collection.objects.link(co)
co.location = (0, -3, 2)
co.rotation_euler = (math.radians(60), 0, 0)
scene.camera = co

w = bpy.data.worlds.new("W")
scene.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (0.04, 0.04, 0.06, 1)
    bg.inputs['Strength'].default_value = 0.3

# --- Mesh ---
bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.3, location=(0,0,0.15), vertices=32)
cyl = bpy.context.active_object
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0.8, 0.4, 0.5), segments=24, ring_count=16)
sph = bpy.context.active_object
bpy.ops.object.shade_smooth()

# --- Simplified leather material (noise only, no Voronoi) ---
mat = bpy.data.materials.new("Leather_Brown")
mat.use_nodes = True
nd = mat.node_tree.nodes
ln = mat.node_tree.links
for n in list(nd):
    nd.remove(n)

out = nd.new('ShaderNodeOutputMaterial'); out.location = (600, 0)
bsdf = nd.new('ShaderNodeBsdfPrincipled'); bsdf.location = (300, 0)
bsdf.inputs['Roughness'].default_value = 0.75
bsdf.inputs['Metallic'].default_value = 0.0

tc = nd.new('ShaderNodeTexCoord'); tc.location = (-600, 0)
nz = nd.new('ShaderNodeTexNoise'); nz.location = (-350, 0)
nz.inputs['Scale'].default_value = 25
nz.inputs['Detail'].default_value = 12
nz.inputs['Roughness'].default_value = 0.6

rp = nd.new('ShaderNodeValToRGB'); rp.location = (-100, 0)
rp.color_ramp.elements[0].color = (0.12, 0.05, 0.02, 1)
rp.color_ramp.elements[1].color = (0.32, 0.14, 0.05, 1)

ln.new(tc.outputs['Object'], nz.inputs['Vector'])
ln.new(nz.outputs['Fac'], rp.inputs['Fac'])
ln.new(rp.outputs['Color'], bsdf.inputs['Base Color'])
ln.new(nz.outputs['Fac'], bsdf.inputs['Roughness'])
ln.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

for mo in (cyl, sph):
    mo.data.materials.clear()
    mo.data.materials.append(mat)

# --- Render ---
png = os.path.join(OUT, "preview_leather_brown.png")
scene.render.filepath = png
bpy.ops.render.render(write_still=True)
print(f"OK preview -> {png}", flush=True)

bl = os.path.join(OUT, "leather_brown.blend")
bpy.ops.wm.save_as_mainfile(filepath=bl)
print(f"OK blend   -> {bl}", flush=True)
print("DONE: leather_brown (low)", flush=True)
