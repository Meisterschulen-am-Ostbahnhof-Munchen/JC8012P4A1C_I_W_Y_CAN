"""Photo-like renderings of the JC8012P4A1C enclosure with Blender (Cycles).

1. python make_textures.py                       (tex/foil.png from the Folika drawing, tex/screen.png)
2. ASSY_EXPORT=1 freecad.exe ../make_assembly.py (parts as STL into cache/variant<n>/)
3. blender --background --python render_blender.py -- <variant> <view> [samples] [width]
   variant: 1 or 2, view: front | back | keypad
   Output: ../img/render_variant<n>_<view>.png (transparent background with shadow)

Coordinates of the STL files: frame coordinates in mm (see ../../mechanics/README.md),
x = long side (+x right seen from the front), +y = top, +z = towards the front (glass at z = 25).
In Blender the unit stands upright: frame y -> world Z, frame z -> world -Y (front faces -Y).
"""
import bpy
import bmesh
import json
import math
import os
import sys
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VARIANT = args[0] if len(args) > 0 else "2"
VIEW = args[1] if len(args) > 1 else "front"
SAMPLES = int(args[2]) if len(args) > 2 else 256
WIDTH = int(args[3]) if len(args) > 3 else 1600
CACHE = os.path.join(HERE, "cache", "variant" + VARIANT)
TEX = os.path.join(HERE, "tex")
OUT = args[4] if len(args) > 4 else os.path.join(HERE, "..", "img", "render_variant%s_%s.png" % (VARIANT, VIEW))

XK = 148.2               # keypad centre x (frame coordinates)
FOIL_Z = 23.0           # top of the foil
ACTIVE = (216.96, 135.36)   # active area of the LCD, centred on the glass

# frame (mm) -> world (m), unit standing upright
TO_WORLD = Matrix.Scale(0.001, 4) @ Matrix.Rotation(math.radians(90), 4, "X")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


# ------------------------------------------------------------------ materials
def principled(name, color, rough=0.5, metal=0.0, coat=0.0, alpha_tr=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = alpha_tr
    b.inputs["IOR"].default_value = ior
    return m


def pa12():
    """MJF PA12: matt grey with a fine grain"""
    m = principled("PA12", (0.16, 0.165, 0.17), rough=0.82)
    nt = m.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4000.0
    noise.inputs["Detail"].default_value = 2.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    return m


def image_material(name, path, emission=0.0, rough=0.35, coat=0.0):
    m = principled(name, (1, 1, 1), rough=rough, coat=coat)
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.interpolation = "Cubic"
    b = nt.nodes["Principled BSDF"]
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    if emission:
        nt.links.remove(b.inputs["Base Color"].links[0])
        b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
        nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emission
    return m


MAT = {
    "frame": pa12(),
    "glass": principled("GlassBlack", (0.004, 0.004, 0.005), rough=0.03, coat=1.0, ior=1.52),
    "disp": principled("DisplayMetal", (0.03, 0.03, 0.035), rough=0.45, metal=0.6),
    "brass": principled("Brass", (0.80, 0.62, 0.30), rough=0.3, metal=1.0),
    "steel": principled("Steel", (0.75, 0.75, 0.77), rough=0.28, metal=1.0),
    "nickel": principled("Nickel", (0.70, 0.69, 0.66), rough=0.22, metal=1.0),
    "mask": principled("SolderMask", (0.02, 0.18, 0.06), rough=0.35, coat=0.5),
    "black": principled("BlackPlastic", (0.02, 0.02, 0.02), rough=0.55),
    "plexi": principled("Plexiglass", (0.95, 0.97, 1.0), rough=0.02, alpha_tr=1.0, ior=1.49),
    "foil": image_material("Foil", os.path.join(TEX, "foil.png"), rough=0.38, coat=0.25),
    "screen": image_material("Screen", os.path.join(TEX, "screen.png"), emission=1.4, rough=0.08, coat=1.0),
}
PART_MAT = {"C": "frame", "3": "nickel", "7": "steel", "9": "steel", "8": "steel", "10": "steel",
            "14": "steel", "15": "steel", "16": "steel", "17": "steel", "1": "steel",
            "13": "black", "B": "mask", "D": "mask", "E": "mask", "19": "plexi", "19f": "foil"}


# ------------------------------------------------------------------ geometry
def load(key):
    path = os.path.join(CACHE, key + ".stl")
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.selected_objects[0]
    o.name = "P_" + key
    o.data.transform(TO_WORLD)
    return o


def assign(o, mat):
    o.data.materials.clear()
    o.data.materials.append(MAT[mat])


def smooth(o, angle=35):
    with bpy.context.temp_override(active_object=o, selected_objects=[o], object=o):
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))


parts = json.load(open(os.path.join(CACHE, "parts.json")))
hide = {"front": (), "back": (), "keypad": ()}[VIEW]
objs = {}
for key in parts:
    if key in hide:
        continue
    o = load(key)
    objs[key] = o
    if key == "A":
        # display envelope: split into glass, metal frame/cover and brass posts
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        for p in [x for x in bpy.context.scene.objects if x.name.startswith("P_A")]:
            zs = [(p.matrix_world @ v.co).y for v in p.data.vertices]   # world -Y = front
            dims = p.dimensions
            if min(zs) < -0.0245:
                assign(p, "glass")
            elif dims.x < 0.01 and dims.z < 0.01:
                assign(p, "brass")
            else:
                assign(p, "disp")
            smooth(p)
    else:
        assign(o, PART_MAT.get(key, "steel"))
        smooth(o)
        if key == "E":
            o.location.y += 0.0006

# foil: planar UV from the frame coordinates (texture = print seen from the front)
if "19f" in objs:
    o = objs["19f"]
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            x, y = lp.vert.co.x * 1000, lp.vert.co.z * 1000      # world X = frame x, world Z = frame y
            lp[uv].uv = ((x - (XK - 24)) / 48.0, (y + 75) / 150.0)
    bm.to_mesh(o.data)
    bm.free()

# screen: emissive plane on the active area, just in front of the glass
bpy.ops.mesh.primitive_plane_add(size=1)
scr = bpy.context.active_object
scr.name = "Screen"
scr.scale = (ACTIVE[0] / 1000, ACTIVE[1] / 1000, 1)
scr.rotation_euler = (math.radians(90), 0, 0)
scr.location = (0, -0.02502, 0)
assign(scr, "screen")

# ------------------------------------------------------------------ world, floor, lights
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
env = wn.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(os.path.dirname(bpy.app.binary_path),
                                              "%d.%d" % bpy.app.version[:2], "datafiles", "studiolights", "world", "studio.exr"))
wn["Background"].inputs["Strength"].default_value = 0.35
world.node_tree.links.new(env.outputs["Color"], wn["Background"].inputs["Color"])

zmin = min((o.matrix_world @ Vector(c)).z for o in bpy.context.scene.objects if o.type == "MESH" for c in o.bound_box)
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, zmin))
floor = bpy.context.active_object
floor.is_shadow_catcher = True


def area(name, loc, energy, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size
    d.color = color
    o = bpy.data.objects.new(name, d)
    scene.collection.objects.link(o)
    o.location = loc
    direction = Vector((0, 0, 0)) - Vector(loc)
    o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return o


area("Key", (-0.6, -0.7, 0.6), 14, 0.6, (1.0, 0.97, 0.92))
area("Fill", (0.8, -0.5, 0.2), 5, 0.8, (0.9, 0.95, 1.0))
area("Rim", (0.3, 0.6, 0.5), 10, 0.5)

# ------------------------------------------------------------------ camera
CAMS = {   # direction from the unit to the camera (world), lens mm
    "front": ((0.38, -1.0, 0.16), 100),
    "back": ((0.50, 1.0, 0.25), 100),
    "keypad": ((0.60, -1.0, 0.22), 135),
}
cdir, lens = CAMS[VIEW]
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = lens
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cdir = Vector(cdir).normalized()
cam.rotation_euler = (-cdir).to_track_quat("-Z", "Y").to_euler()
scene.render.resolution_x = WIDTH
scene.render.resolution_y = int(WIDTH * 2 / 3)
pts = []
for o in bpy.context.scene.objects:
    if o.type == "MESH" and o is not floor and (VIEW != "keypad" or o.name in ("P_19f", "P_19", "P_C")):
        if o.name in ("P_B", "P_E", "P_1"):       # inside the unit, not needed for the outline
            continue
        vs = o.data.vertices
        step = max(1, len(vs) // 4000)
        pts += [o.matrix_world @ vs[i].co for i in range(0, len(vs), step)]
if VIEW == "keypad":
    pts = [p for p in pts if p.x > 0.0]
bpy.context.view_layer.update()                # apply the camera rotation before fitting
dg = bpy.context.evaluated_depsgraph_get()
loc, _ = cam.camera_fit_coords(dg, [c for p in pts for c in p])
cam.location = loc
ctr = sum(pts, Vector()) / len(pts)
fwd = (-cdir).normalized()                     # viewing direction of the camera
depth = (ctr - loc).dot(fwd)
cam.location = loc - fwd * depth * (0.30 if VIEW == "keypad" else 0.12)   # margin along the viewing axis
from bpy_extras.object_utils import world_to_camera_view
for _ in range(4):                              # pan so the unit sits in the middle of the picture
    bpy.context.view_layer.update()
    nd = [world_to_camera_view(scene, cam, p) for p in pts]
    du = (min(v.x for v in nd) + max(v.x for v in nd)) / 2 - 0.5
    dv = (min(v.y for v in nd) + max(v.y for v in nd)) / 2 - 0.5
    d = (ctr - cam.location).dot(fwd)
    fw = d * 36.0 / cam_data.lens                 # visible width at the depth of the unit (sensor 36 mm)
    fh = fw * scene.render.resolution_y / scene.render.resolution_x
    rot = cam.matrix_world.to_3x3()
    cam.location += rot @ Vector((du * fw, dv * fh, 0))
cam_data.dof.focus_distance = (ctr - cam.location).dot(fwd)
print('CAM', VIEW, tuple(round(v, 3) for v in cam.location), 'ctr', tuple(round(v, 3) for v in ctr), 'focus', round(cam_data.dof.focus_distance, 3))
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 16

# ------------------------------------------------------------------ render
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.device = "CPU"
scene.render.film_transparent = True
scene.render.resolution_x = WIDTH
scene.render.resolution_y = int(WIDTH * 2 / 3)
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = os.path.abspath(OUT)
bpy.ops.render.render(write_still=True)
print("RENDERED", os.path.abspath(OUT))
