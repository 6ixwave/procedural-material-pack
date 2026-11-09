import bpy, os

out = r"C:\Users\aleks\Downloads\earn-auto\blender_assets\output"
os.makedirs(out, exist_ok=True)

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Base plane (2x2 at origin)
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
plane = bpy.context.active_object
plane.name = "BasePlane"
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cube_project()
bpy.ops.object.mode_set(mode='OBJECT')

# Camera: top-down view of the plane
bpy.ops.object.camera_add(location=(0, 0, 3))
cam = bpy.context.active_object
cam.name = "TopCam"
cam.data.lens = 50
bpy.context.scene.camera = cam

# Render settings (Blender 5.2)
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 16
bpy.context.scene.render.resolution_x = 512
bpy.context.scene.render.resolution_y = 512
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.view_settings.view_transform = 'Standard'

# Add a simple sun light so materials are visible
bpy.ops.object.light_add(type='SUN', location=(2, 2, 5))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (0.8, 0.3, 0.5)

def make_mat(name, setup_fn):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out_node = nt.nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (600, 0)
    bpr = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bpr.location = (300, 0)
    nt.links.new(bpr.outputs['BSDF'], out_node.inputs['Surface'])
    setup_fn(nt, bpr)
    return mat

def add_noise(nt, bpr, scale=5, detail=8, rough=0.6, metallic=0.0, c1=None, c2=None):
    tex = nt.nodes.new('ShaderNodeTexNoise')
    tex.location = (-200, 0)
    tex.inputs['Scale'].default_value = scale
    tex.inputs['Detail'].default_value = detail
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-50, 0)
    if c1: ramp.color_ramp.elements[0].color = c1
    if c2: ramp.color_ramp.elements[1].color = c2
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bpr.inputs['Base Color'])
    bpr.inputs['Roughness'].default_value = rough
    bpr.inputs['Metallic'].default_value = metallic

def add_wave(nt, bpr, scale=3, dist=10, rough=0.5, c1=(0.3,0.2,0.1,1), c2=(0.6,0.4,0.2,1)):
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.location = (-300, 0)
    wave.inputs['Scale'].default_value = scale
    wave.inputs['Distortion'].default_value = dist
    texco = nt.nodes.new('ShaderNodeTexCoord')
    texco.location = (-500, 0)
    nt.links.new(texco.outputs['Object'], wave.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-100, 0)
    ramp.color_ramp.elements[0].color = c1
    ramp.color_ramp.elements[1].color = c2
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bpr.inputs['Base Color'])
    bpr.inputs['Roughness'].default_value = rough

def add_voronoi(nt, bpr, scale=8, rough=0.7, c1=(0.4,0.4,0.4,1), c2=(0.7,0.7,0.7,1)):
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.location = (-200, 0)
    vor.inputs['Scale'].default_value = scale
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-50, 0)
    ramp.color_ramp.elements[0].color = c1
    ramp.color_ramp.elements[1].color = c2
    nt.links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bpr.inputs['Base Color'])
    bpr.inputs['Roughness'].default_value = rough

def add_checker(nt, bpr, scale=10, rough=0.5, c1=(0.8,0.1,0.1,1), c2=(0.9,0.9,0.9,1)):
    chk = nt.nodes.new('ShaderNodeTexChecker')
    chk.location = (-200, 0)
    chk.inputs['Scale'].default_value = scale
    chk.inputs['Color1'].default_value = c1
    chk.inputs['Color2'].default_value = c2
    nt.links.new(chk.outputs['Color'], bpr.inputs['Base Color'])
    bpr.inputs['Roughness'].default_value = rough

def add_gradient(nt, bpr, rough=0.3, c1=(0.1,0.3,0.8,1), c2=(0.5,0.8,1,1)):
    grad = nt.nodes.new('ShaderNodeTexGradient')
    grad.location = (-300, 0)
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.location = (-450, 0)
    texco = nt.nodes.new('ShaderNodeTexCoord')
    texco.location = (-600, 0)
    nt.links.new(texco.outputs['UV'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], grad.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-100, 0)
    ramp.color_ramp.elements[0].color = c1
    ramp.color_ramp.elements[1].color = c2
    nt.links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bpr.inputs['Base Color'])
    bpr.inputs['Roughness'].default_value = rough

def set_glass(bpr, color, rough, trans, ior):
    bpr.inputs['Base Color'].default_value = color
    bpr.inputs['Roughness'].default_value = rough
    bpr.inputs['Transmission Weight'].default_value = trans
    bpr.inputs['IOR'].default_value = ior

# === 32 NEW MATERIALS ===
materials = [
    ("Wood_Maple", lambda nt,b: add_wave(nt,b,4,6,0.4,(0.7,0.55,0.3,1),(0.85,0.7,0.5,1))),
    ("Wood_Cherry", lambda nt,b: add_wave(nt,b,5,8,0.35,(0.5,0.2,0.1,1),(0.7,0.35,0.2,1))),
    ("Wood_Pine", lambda nt,b: add_wave(nt,b,3,4,0.5,(0.6,0.5,0.3,1),(0.8,0.65,0.4,1))),
    ("Wood_Ebony", lambda nt,b: add_wave(nt,b,6,12,0.3,(0.05,0.03,0.02,1),(0.15,0.1,0.08,1))),
    ("Wood_Bamboo", lambda nt,b: add_wave(nt,b,8,3,0.45,(0.5,0.6,0.2,1),(0.7,0.8,0.3,1))),
    ("Wood_Teak", lambda nt,b: add_wave(nt,b,4,7,0.4,(0.4,0.25,0.1,1),(0.6,0.4,0.2,1))),
    ("Metal_Titanium", lambda nt,b: add_noise(nt,b,12,6,0.3,1.0,(0.6,0.6,0.65,1),(0.85,0.85,0.9,1))),
    ("Metal_Bronze", lambda nt,b: add_noise(nt,b,8,4,0.35,1.0,(0.7,0.45,0.2,1),(0.9,0.65,0.35,1))),
    ("Metal_Chrome", lambda nt,b: add_noise(nt,b,20,3,0.1,1.0,(0.85,0.85,0.9,1),(0.95,0.95,0.98,1))),
    ("Metal_Iron_Rust", lambda nt,b: add_noise(nt,b,6,10,0.8,0.3,(0.5,0.2,0.05,1),(0.7,0.35,0.1,1))),
    ("Metal_Silver", lambda nt,b: add_noise(nt,b,15,4,0.2,1.0,(0.8,0.8,0.85,1),(0.95,0.95,0.98,1))),
    ("Metal_Copper_Oxide", lambda nt,b: add_noise(nt,b,7,8,0.6,0.5,(0.3,0.5,0.4,1),(0.6,0.7,0.5,1))),
    ("Metal_Nickel", lambda nt,b: add_noise(nt,b,10,5,0.25,1.0,(0.7,0.7,0.73,1),(0.9,0.9,0.92,1))),
    ("Metal_Steel_Brushed", lambda nt,b: add_wave(nt,b,15,2,0.3,(0.6,0.6,0.62,1),(0.8,0.8,0.82,1))),
    ("Stone_Slate", lambda nt,b: add_voronoi(nt,b,10,0.8,(0.15,0.15,0.18,1),(0.3,0.3,0.35,1))),
    ("Stone_Limestone", lambda nt,b: add_noise(nt,b,4,6,0.7,0.0,(0.7,0.65,0.55,1),(0.85,0.8,0.7,1))),
    ("Stone_Sandstone", lambda nt,b: add_noise(nt,b,6,8,0.75,0.0,(0.8,0.65,0.4,1),(0.9,0.75,0.5,1))),
    ("Stone_Basalt", lambda nt,b: add_voronoi(nt,b,12,0.85,(0.05,0.05,0.06,1),(0.15,0.15,0.16,1))),
    ("Stone_Travertine", lambda nt,b: add_wave(nt,b,5,6,0.6,(0.8,0.75,0.65,1),(0.9,0.85,0.75,1))),
    ("Stone_Quartz", lambda nt,b: add_voronoi(nt,b,8,0.4,(0.9,0.88,0.85,1),(1,0.98,0.95,1))),
    ("Glass_Smoke", lambda nt,b: set_glass(b,(0.3,0.3,0.3,1),0.05,1.0,1.52)),
    ("Glass_Amber", lambda nt,b: set_glass(b,(0.8,0.5,0.1,1),0.05,1.0,1.5)),
    ("Glass_Frosted", lambda nt,b: set_glass(b,(0.95,0.95,0.95,1),0.3,0.9,1.5)),
    ("Glass_Crystal", lambda nt,b: set_glass(b,(1,1,1,1),0.02,1.0,1.6)),
    ("Organic_Mushroom", lambda nt,b: add_voronoi(nt,b,6,0.6,(0.8,0.3,0.1,1),(0.9,0.7,0.5,1))),
    ("Organic_Moss", lambda nt,b: add_noise(nt,b,10,12,0.8,0.0,(0.1,0.3,0.05,1),(0.2,0.5,0.1,1))),
    ("Organic_Coral", lambda nt,b: add_voronoi(nt,b,8,0.5,(0.9,0.4,0.3,1),(1,0.7,0.6,1))),
    ("Organic_Rubber", lambda nt,b: add_noise(nt,b,5,4,0.4,0.0,(0.05,0.05,0.05,1),(0.15,0.15,0.15,1))),
    ("Textile_Denim", lambda nt,b: add_checker(nt,b,20,0.6,(0.1,0.15,0.3,1),(0.15,0.2,0.35,1))),
    ("Textile_Silk", lambda nt,b: add_gradient(nt,b,0.15,(0.8,0.2,0.4,1),(1,0.6,0.7,1))),
    ("Textile_Wool", lambda nt,b: add_noise(nt,b,15,10,0.9,0.0,(0.6,0.5,0.4,1),(0.75,0.65,0.55,1))),
    ("Textile_Linen", lambda nt,b: add_checker(nt,b,15,0.5,(0.85,0.8,0.7,1),(0.9,0.85,0.75,1))),
]

print(f"Generating {len(materials)} materials (Blender 5.2, Cycles, top-down cam)...")
for i, (name, fn) in enumerate(materials):
    print(f"  [{i+1}/{len(materials)}] {name}")
    if plane.data.materials:
        plane.data.materials.clear()
    mat = make_mat(name, fn)
    plane.data.materials.append(mat)
    # Save .blend
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{name.lower()}.blend"))
    # Render preview PNG
    bpy.context.scene.render.filepath = os.path.join(out, f"preview_{name.lower()}.png")
    bpy.ops.render.render(write_still=True)

print(f"DONE: {len(materials)} materials -> {out}")
