"""Build the authored railway diorama in Blender and export material-aware FBX groups."""

import json
import math
import random
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Art" / "Models" / "Refined"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(934)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

PALETTE = {
    "Brick": ((0.28, 0.105, 0.055), 0.0, 0.87, "brick", 2.6),
    "Stone": ((0.35, 0.32, 0.26), 0.0, 0.68, "stone", 3.2),
    "Scarlet": ((0.19, 0.014, 0.023), 0.0, 0.32, "scarlet", 2.0),
    "BlackSteel": ((0.018, 0.025, 0.027), 0.78, 0.34, "blacksteel", 2.0),
    "Iron": ((0.029, 0.062, 0.059), 0.2, 0.47, "iron", 2.0),
    "Brass": ((0.40, 0.255, 0.086), 0.85, 0.28, "brass", 1.8),
    "Leather": ((0.26, 0.105, 0.035), 0.0, 0.67, "leather", 0.75),
    "DarkLeather": ((0.115, 0.055, 0.019), 0.0, 0.70, "leather", 0.9),
    "Wood": ((0.20, 0.095, 0.030), 0.0, 0.61, "wood", 1.3),
    "Cream": ((0.79, 0.70, 0.49), 0.1, 0.55, "enamel", 2.0),
    "Lettering": ((0.015, 0.013, 0.01), 0.1, 0.45, None, 1.0),
    "Glass": ((0.11, 0.21, 0.22), 0.0, 0.25, "dirtyglass", 1.0),
    "AmberGlass": ((0.18, 0.10, 0.035), 0.0, 0.32, "dirtyglass", 1.0),
    "Lamp": ((1.0, 0.49, 0.14), 0.0, 0.35, None, 1.0),
    "Gravel": ((0.09, 0.115, 0.12), 0.0, 0.91, "ballast", 1.2),
    "Blanket": ((0.13, 0.009, 0.027), 0.0, 0.95, "cloth", 0.25),
    "RoofPanel": ((0.045, 0.054, 0.048), 0.3, 0.72, "iron", 2.0),
    "Puddle": ((0.10, 0.12, 0.12), 0.4, 0.075, None, 1.0),
}
MATERIALS = {}
for name, (color, metallic, roughness, texture, scale) in PALETTE.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if texture:
        path = ROOT / "Art" / "Textures" / f"{texture}.png"
        if not path.is_file():
            raise FileNotFoundError(f"Generated texture required before modeling: {path}")
        node = material.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(path), check_existing=True)
        if name not in ("Glass", "AmberGlass"):
            material.node_tree.links.new(node.outputs["Color"], shader.inputs["Base Color"])
    MATERIALS[name] = material

meshes = defaultdict(lambda: {"verts": [], "faces": [], "uv": []})
GROUP = "Architecture"


def face(material, points, uv=None):
    bucket = meshes[(GROUP, material)]
    start = len(bucket["verts"])
    vertices = [Vector(p) for p in points]
    bucket["verts"].extend(vertices)
    bucket["faces"].append(tuple(range(start, start + len(points))))
    if uv is None:
        normal = (vertices[1] - vertices[0]).cross(vertices[2] - vertices[0])
        axis = max(range(3), key=lambda i: abs(normal[i]))
        axes = [i for i in range(3) if i != axis]
        scale = PALETTE[material][4]
        uv = [(v[axes[0]] / scale, v[axes[1]] / scale) for v in vertices]
    bucket["uv"].extend(uv)


def box(material, center, size):
    x, y, z = center
    a, b, c = [v / 2 for v in size]
    v = [(x-a, y-b, z-c), (x+a, y-b, z-c), (x+a, y+b, z-c), (x-a, y+b, z-c),
         (x-a, y-b, z+c), (x+a, y-b, z+c), (x+a, y+b, z+c), (x-a, y+b, z+c)]
    for indexes in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                    (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        face(material, [v[i] for i in indexes])


def cylinder(material, a, b, radius, segments=24, radius_end=None):
    a, b = Vector(a), Vector(b)
    direction = (b-a).normalized()
    ref = Vector((0, 0, 1)) if abs(direction.z) < 0.9 else Vector((0, 1, 0))
    u = direction.cross(ref).normalized()
    v = direction.cross(u).normalized()
    r2 = radius if radius_end is None else radius_end
    ring1 = [a + radius * (u*math.cos(i*math.tau/segments) + v*math.sin(i*math.tau/segments))
             for i in range(segments)]
    ring2 = [b + r2 * (u*math.cos(i*math.tau/segments) + v*math.sin(i*math.tau/segments))
             for i in range(segments)]
    face(material, list(reversed(ring1)))
    face(material, ring2)
    for i in range(segments):
        j = (i+1) % segments
        face(material, [ring1[i], ring1[j], ring2[j], ring2[i]],
             [(i/segments, 0), ((i+1)/segments, 0), ((i+1)/segments, (b-a).length),
              (i/segments, (b-a).length)])


def tube(material, points, radius, segments=10):
    for a, b in zip(points, points[1:]):
        cylinder(material, a, b, radius, segments)


def ring(material, center, radius, width, plane="XZ", segments=64):
    c = Vector(center)
    axes = {"XZ": ((1, 0, 0), (0, 0, 1)),
            "YZ": ((0, 1, 0), (0, 0, 1)),
            "XY": ((1, 0, 0), (0, 1, 0))}
    u, v = [Vector(x) for x in axes[plane]]
    points = [c + radius * (u*math.cos(i*math.tau/segments) + v*math.sin(i*math.tau/segments))
              for i in range(segments+1)]
    tube(material, points, width, 8)


def arch(material, y, base, radius_x, radius_z, width, center_x=-2):
    points = [(center_x+radius_x*math.cos(t), y, base+radius_z*math.sin(t))
              for t in [i*math.pi/48 for i in range(49)]]
    tube(material, points, width, 8)


def rivet(material, position, direction=(0, -1, 0), radius=0.022):
    p, d = Vector(position), Vector(direction)
    cylinder(material, p, p+d*0.022, radius, 8, radius*0.7)


def text(body, position, size, material, rotation=(math.pi/2, 0, 0), align="CENTER"):
    curve = bpy.data.curves.new("Inscription", "FONT")
    curve.body = body
    curve.size = size
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.extrude = 0.0015
    curve.resolution_u = 8
    font = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
    if font.is_file():
        curve.font = bpy.data.fonts.load(str(font), check_existing=True)
    else:
        print("FONT_NOTICE: Times New Roman unavailable; using Blender's built-in typeface.")
    obj = bpy.data.objects.new("Inscription", curve)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = rotation
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    for polygon in mesh.polygons:
        face(material, [obj.matrix_world @ mesh.vertices[i].co for i in polygon.vertices])
    evaluated.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)


# Masonry is segmented around real openings rather than painted onto a solid wall.
box("Stone", (2.25, 28, 0.34), (5.5, 78, 0.68))
box("Stone", (-7.6, 28, 0.30), (4.6, 78, 0.60))
box("Gravel", (-2.7, 28, -0.15), (4.5, 78, 0.30))
for row in range(-10, 48):
    offset = 0.45 if row % 2 else 0.0
    for col in range(6):
        x = 0.11 + col*0.87 + offset
        if x + 0.43 < 4.9:
            box("Stone", (x, row+0.5, 0.681+random.uniform(-0.002, 0.002)),
                (0.852, 0.977, 0.016))
for y in range(-10, 68, 2):
    box("Cream", (-0.46, y, 0.69), (0.29, 1.98, 0.07))
    box("Stone", (-0.59, y, 0.46), (0.15, 1.98, 0.48))
for side in (4.95, -10.0):
    for y in range(-8, 67, 5):
        box("Brick", (side, y, 4.25), (0.60, 0.95, 7.15))
        box("Stone", (side-0.04, y, 0.99), (0.71, 1.12, 0.52))
        box("Stone", (side-0.04, y, 6.65), (0.77, 1.12, 0.24))
        box("Brick", (side, y+2.5, 1.2), (0.50, 4.05, 1.00))
        box("Brick", (side, y+2.5, 6.85), (0.50, 4.05, 1.75))
        for offset in (1.0, 4.0):
            box("Brick", (side, y+offset, 3.8), (0.55, 1.0, 4.2))
        # Fill the curved spandrel above the arched glass opening.
        for i in range(20):
            yy = y + 1.50 + i*0.10
            arc_top = 4.8 + math.sqrt(max(0, 1.01**2 - (yy+0.05-y-2.5)**2))
            if arc_top < 6.05:
                box("Brick", (side, yy+0.1, (6.05+arc_top)/2),
                    (0.5, 0.102, 6.05-arc_top))
        inward = -1 if side > 0 else 1
        x = side + inward*0.33
        box("Stone", (x, y+2.5, 1.69), (0.45, 2.25, 0.20))
        for t in range(18):
            a, b = t*math.pi/18+0.006, (t+1)*math.pi/18-0.006
            for xx in (x-0.10, x+0.10):
                points = [(xx, y+2.5+r*math.cos(theta), 4.8+r*math.sin(theta))
                          for r, theta in ((1.0, a), (1.0, b), (1.24, b), (1.24, a))]
                face("Brick", points if xx < x else list(reversed(points)))
            for r in (1.0, 1.24):
                face("Brick", [(xx, y+2.5+r*math.cos(theta), 4.8+r*math.sin(theta))
                               for xx, theta in ((x-.1, a), (x+.1, a), (x+.1, b), (x-.1, b))])
        GROUP = "Windows"
        box("AmberGlass", (x+inward*0.015, y+2.5, 3.22), (0.055, 1.95, 3.02))
        points = [(x, y+2.5, 4.8)] + [
            (x, y+2.5+0.97*math.cos(t*math.pi/32), 4.8+0.97*math.sin(t*math.pi/32))
            for t in range(33)]
        face("Glass", points)
        for offset in (-0.95, -0.475, 0, 0.475, 0.95):
            top = 4.8+math.sqrt(max(0, 0.95**2-offset**2))
            box("Iron", (x+inward*0.055, y+2.5+offset, (1.8+top)/2),
                (0.09, 0.05, top-1.8))
        for z in (2.5, 3.3, 4.1, 4.8, 5.45):
            span = 1.9 if z <= 4.8 else 2*math.sqrt(max(0, 0.95**2-(z-4.8)**2))
            box("Iron", (x+inward*0.055, y+2.5, z), (0.10, span, 0.06))
        GROUP = "Architecture"

GROUP = "Roof"
for y in range(-8, 70, 5):
    arch("Iron", y, 6.65, 7.4, 5.2, 0.10, -2.55)
    arch("Iron", y, 6.65, 7.4, 4.72, 0.065, -2.55)
    for i in range(17):
        t = (i+0.5)*math.pi/17
        p = (-2.55+7.4*math.cos(t), y, 6.65+5.2*math.sin(t))
        t2 = (i+1)*math.pi/17
        q = (-2.55+7.4*math.cos(t2), y, 6.65+4.72*math.sin(t2))
        tube("Iron", [p, q], 0.035, 6)
    for x in (-9.65, 4.55):
        box("Iron", (x, y, 3.7), (0.18, 0.26, 6.0))
        box("Iron", (x, y, 0.90), (0.43, 0.46, 0.40))
        box("Brass", (x, y, 6.5), (0.38, 0.43, 0.16))
        for s in (-1, 1):
            tube("Iron", [(x, y, 5.4), (x, y+s*1.2, 6.55)], 0.07)
    for i in range(20):
        a, b = i*math.pi/20, (i+1)*math.pi/20
        pts = [(-2.55+7.4*math.cos(t), yy, 6.65+5.2*math.sin(t))
               for t, yy in ((a, y), (b, y), (b, y+5), (a, y+5))]
        face("Glass" if 7 <= i <= 12 and y % 15 != 2 else "RoofPanel", pts)
        if i in (4, 6, 13, 15):
            for offset in (1.25, 2.5, 3.75):
                arch("Iron", y+offset, 6.65, 7.4, 5.2, 0.025, -2.55)
for i in range(21):
    t = i*math.pi/20
    cylinder("Iron", (-2.55+7.4*math.cos(t), -8, 6.65+5.2*math.sin(t)),
             (-2.55+7.4*math.cos(t), 72, 6.65+5.2*math.sin(t)), 0.045, 8)

GROUP = "FarWall"
for x in (-9.7, -7.2, -4.7, -2.2, 0.3, 2.8, 4.65):
    box("Iron", (x, 66, 5.1), (0.065, 0.14, 8.7))
box("Glass", (-2.5, 66.1, 5.1), (14.4, 0.10, 8.7))
for z in (2.5, 4.5, 6.5, 8.5):
    box("Iron", (-2.5, 66, z), (14.4, 0.14, 0.075))

GROUP = "Track"
for x in (-3.42, -1.96):
    box("BlackSteel", (x, 28, 0.10), (0.12, 78, 0.15))
    box("BlackSteel", (x, 28, 0.03), (0.19, 78, 0.04))
for i in range(112):
    y = -10+i*0.7
    box("Wood", (-2.69, y, -0.015), (2.65, 0.22, 0.17))
    for x in (-3.42, -1.96):
        box("BlackSteel", (x, y, 0.07), (0.26, 0.15, 0.035))
for i in range(9000):
    x, y = random.uniform(-4.82, -0.7), random.uniform(-10, 68)
    radius = random.uniform(0.025, 0.075)
    cylinder("Gravel", (x, y, -0.02), (x+radius*0.3, y, radius*0.7),
             radius, 5, radius*0.65)

GROUP = "Locomotive"
TX = -2.69
box("BlackSteel", (TX, 8.0, 1.05), (1.55, 10.4, 0.40))
box("Scarlet", (TX, 7.65, 1.55), (2.76, 10.8, 0.19))
cylinder("Scarlet", (TX, 4.35, 2.80), (TX, 11.75, 2.80), 1.02, 80)
cylinder("BlackSteel", (TX, 3.15, 2.80), (TX, 4.50, 2.80), 1.065, 80)
cylinder("BlackSteel", (TX, 3.02, 2.80), (TX, 3.16, 2.80), 0.985, 80)
ring("BlackSteel", (TX, 2.98, 2.80), 0.985, 0.055)
ring("Brass", (TX, 2.965, 2.80), 1.018, 0.012)
for i in range(32):
    t = i*math.tau/32
    rivet("BlackSteel", (TX+0.91*math.cos(t), 2.94, 2.80+0.91*math.sin(t)), radius=0.027)
for y in (4.45, 6.25, 8.1, 10.3, 11.60):
    ring("BlackSteel", (TX, y, 2.8), 1.035, 0.027)
for y in (4.2, 7.7, 10.0):
    height = 4.62 if y == 4.2 else 4.08
    cylinder("BlackSteel" if y == 4.2 else "Brass",
             (TX, y, 3.64), (TX, y, height), 0.29 if y == 4.2 else 0.22, 48,
             0.39 if y == 4.2 else 0.16)
    ring("BlackSteel" if y == 4.2 else "Brass", (TX, y, height),
         0.39 if y == 4.2 else 0.18, 0.045, "XY")
cylinder("Brass", (TX-0.30, 8.2, 3.7), (TX-0.30, 8.2, 4.12), 0.055, 16)
tube("Brass", [(TX+0.75, 4.2, 3.42), (TX+0.82, 7, 3.41),
               (TX+0.82, 10.7, 3.41), (TX+0.95, 11.1, 2.2)], 0.026)
for side in (-1, 1):
    x = TX+side*1.12
    tube("BlackSteel", [(x, 3.95, 2.9), (x, 4.5, 2.45), (x, 5.1, 1.4)], 0.10)
    cylinder("BlackSteel", (x, 4.1, 1.0), (x, 5.0, 1.0), 0.26, 32)
    cylinder("Brass", (x, 4.96, 1.0), (x, 6.3, 1.0), 0.055, 16)
    for y in [3.2+i*0.33 for i in range(30)]:
        rivet("BlackSteel", (TX+side*1.39, y, 1.54), (side, 0, 0), 0.026)
    for y in (3.8, 6, 8, 10, 11.5):
        box("BlackSteel", (TX+side*0.91, y, 3.36), (0.07, 0.045, 0.12))
    cylinder("BlackSteel", (TX+side*0.92, 3.8, 3.45),
             (TX+side*0.92, 11.5, 3.45), 0.025, 12)
box("Scarlet", (TX, 2.62, 0.96), (2.9, 0.28, 0.62))
for x in (TX-1.06, TX+1.06):
    cylinder("BlackSteel", (x, 2.56, 0.96), (x, 2.10, 0.96), 0.15, 24)
    cylinder("BlackSteel", (x, 2.10, 0.96), (x, 1.96, 0.96), 0.25, 40)
    ring("BlackSteel", (x, 2.09, 0.96), 0.16, 0.030)
for row in (0.73, 1.17):
    for i in range(13):
        rivet("BlackSteel", (TX-1.28+i*0.21, 2.46, row), radius=0.025)
tube("BlackSteel", [(TX, 2.55, 1), (TX, 1.96, 0.65), (TX+0.10, 2.12, 0.42)], 0.053)
tube("BlackSteel", [(TX-0.45, 2.53, 1.3), (TX-0.4, 2.15, 0.63),
                    (TX-0.25, 2.02, 0.45)], 0.044)
cylinder("Brass", (TX, 2.91, 2.8), (TX, 2.73, 2.8), 0.08, 24)
for t in (0, math.pi/2):
    cylinder("Brass", (TX-0.28*math.cos(t), 2.72, 2.80-0.28*math.sin(t)),
             (TX+0.28*math.cos(t), 2.72, 2.80+0.28*math.sin(t)), 0.025, 12)
for z in (2.3, 3.3):
    box("BlackSteel", (TX+0.65, 2.90, z), (0.4, 0.07, 0.065))
text("5979", (TX, 2.913, 2.23), 0.12, "Brass")

GROUP = "Wheels"
for y, radius in ((3.75, 0.48), (5.5, 0.82), (7.45, 0.82), (9.4, 0.82), (11.75, 0.5)):
    z = radius+0.15
    cylinder("BlackSteel", (TX-1.12, y, z), (TX+1.12, y, z), 0.105, 16)
    for side in (-1, 1):
        x = TX+side*1.15
        ring("BlackSteel", (x, y, z), radius, 0.083, "YZ", 64)
        ring("Scarlet", (x+side*0.03, y, z), radius-0.1, 0.045, "YZ", 48)
        cylinder("Scarlet", (x-side*0.05, y, z), (x+side*0.08, y, z), 0.145, 24)
        for i in range(18):
            t = i*math.tau/18
            cylinder("Scarlet", (x, y+0.12*math.cos(t), z+0.12*math.sin(t)),
                     (x, y+(radius-0.12)*math.cos(t), z+(radius-0.12)*math.sin(t)),
                     0.035, 6)
        if radius > 0.7:
            cylinder("Brass", (x, y+0.28, z-0.18), (x+side*0.19, y+0.28, z-0.18),
                     0.10, 20)
for side in (-1, 1):
    x = TX+side*1.36
    tube("BlackSteel", [(x, 5.78, 0.79), (x, 7.73, 0.79), (x, 9.68, 0.79)], 0.07, 8)
    tube("Brass", [(x+side*0.025, 4.85, 1.03), (x+side*0.025, 7.72, 0.79)], 0.048, 8)
    for y in (5.78, 7.73, 9.68):
        cylinder("BlackSteel", (x, y, 0.79), (x+side*0.08, y, 0.79), 0.095, 20)

GROUP = "CabTender"
box("Scarlet", (TX, 12.8, 2.05), (2.76, 2.1, 1.02))
box("Scarlet", (TX, 13.76, 3.1), (2.76, 0.15, 1.45))
for side in (-1, 1):
    x = TX+side*1.34
    for y in (11.9, 13.7):
        box("Scarlet", (x, y, 3.11), (0.12, 0.17, 1.37))
    box("Scarlet", (x, 12.8, 3.72), (0.12, 1.9, 0.23))
    box("Glass", (x, 12.8, 3.15), (0.045, 1.55, 0.92))
    box("Brass", (x+side*0.035, 12.8, 2.08), (0.018, 0.58, 0.3))
    for z, xx in ((0.55, 1.6), (0.90, 1.48), (1.24, 1.40)):
        box("BlackSteel", (TX+side*xx, 12.5, z), (0.38, 0.72, 0.09))
box("BlackSteel", (TX, 12.85, 3.96), (3.0, 2.6, 0.16))
box("Scarlet", (TX, 16.35, 2.08), (2.65, 4.3, 1.55))
box("BlackSteel", (TX, 16.35, 2.92), (2.42, 4.08, 0.25))
for i in range(180):
    x, y = TX+random.uniform(-1.1, 1.1), random.uniform(14.6, 18.1)
    cylinder("BlackSteel", (x, y, 2.92), (x, y, 3.10+random.random()*0.15),
             random.uniform(0.07, 0.14), 5, 0.025)
for y in (14.9, 17.65):
    for side in (-1, 1):
        ring("BlackSteel", (TX+side*1.12, y, 0.75), 0.60, 0.08, "YZ", 32)

GROUP = "Carriages"
for start in (19.0, 32.2, 45.4):
    box("Scarlet", (TX, start+6.25, 1.75), (2.73, 12.5, 1.24))
    box("BlackSteel", (TX, start+6.25, 1.09), (2.45, 12.5, 0.27))
    for side in (-1, 1):
        x = TX+side*1.365
        for i in range(9):
            y = start+0.7+i*1.35
            box("Wood", (x, y, 2.91), (0.075, 0.12, 1.65))
            box("AmberGlass", (x, y+0.62, 2.95), (0.04, 1.10, 1.18))
            for zz in (2.30, 3.6):
                box("Brass", (x+side*0.02, y+0.62, zz), (0.03, 1.13, 0.045))
        box("Scarlet", (x, start+6.25, 3.7), (0.12, 12.5, 0.3))
        box("Brass", (x+side*0.055, start+6.25, 2.17), (0.025, 12.5, 0.023))
    for i in range(12):
        a, b = i*math.pi/12, (i+1)*math.pi/12
        face("BlackSteel", [(TX+1.43*math.cos(t), y, 3.75+0.45*math.sin(t))
                           for t, y in ((a, start-0.1), (b, start-0.1),
                                        (b, start+12.6), (a, start+12.6))])
    for y in (start+1.5, start+2.7, start+9.8, start+11):
        for side in (-1, 1):
            ring("BlackSteel", (TX+side*1.12, y, 0.65), 0.5, 0.085, "YZ", 24)


def suitcase(x, y, bottom, width, depth, height, mat="Leather"):
    box(mat, (x, y, bottom+height/2), (width, depth, height))
    for dx in (-width*0.34, width*0.34):
        box("DarkLeather", (x+dx, y-depth/2-0.01, bottom+height/2),
            (0.068, 0.028, height))
        box("DarkLeather", (x+dx, y, bottom+height+0.008), (0.068, depth, 0.025))
        box("Brass", (x+dx, y-depth/2-0.03, bottom+height*0.73),
            (0.095, 0.035, 0.08))
    for dx in (-1, 1):
        for dz in (0.035, height-0.035):
            box("Brass", (x+dx*(width/2-0.035), y-depth/2-0.021, bottom+dz),
                (0.095, 0.018, 0.082))
    tube("DarkLeather", [(x-0.13, y-depth/2-0.045, bottom+height*0.53),
                         (x-0.12, y-depth/2-0.11, bottom+height*0.65),
                         (x+0.12, y-depth/2-0.11, bottom+height*0.65),
                         (x+0.13, y-depth/2-0.045, bottom+height*0.53)], 0.025)
    for i in range(11):
        rivet("Brass", (x-width/2+0.05+i*(width-0.10)/10, y-depth/2-0.025,
                        bottom+0.05), radius=0.008)


GROUP = "Luggage"
cx, cy = 4.02, 0.0
box("Wood", (cx, cy, 1.03), (1.45, 1.12, 0.12))
for side in (-1, 1):
    for yy in (cy-0.38, cy+0.38):
        ring("BlackSteel", (cx+side*0.60, yy, 0.9), 0.20, 0.043, "YZ", 24)
    tube("Brass", [(cx+side*0.63, cy+0.42, 1.03), (cx+side*0.63, cy+0.42, 2.53),
                   (cx+side*0.51, cy+0.42, 2.73), (cx, cy+0.42, 2.83)], 0.035)
suitcase(cx, cy-0.12, 1.09, 1.27, 0.86, 0.70)
suitcase(cx-0.14, cy+0.10, 1.8, 0.98, 0.59, 0.40, "DarkLeather")
suitcase(3.12, 3.00, 0.73, 0.64, 0.36, 0.86)
suitcase(3.86, 3.45, 0.73, 0.79, 0.43, 1.15, "DarkLeather")
box("Blanket", (cx+0.23, cy-0.16, 2.21), (0.78, 0.63, 0.10))
for i in range(22):
    cylinder("Blanket", (cx-0.14+i*0.034, cy-0.47, 2.21),
             (cx-0.14+i*0.034, cy-0.50, 2.05-random.random()*0.08), 0.008, 5)
# Delicate cage bars and domed crown remain actual geometry.
gx, gy, bottom = cx-0.15, cy+0.08, 2.27
for z in (bottom, bottom+0.08, bottom+0.48, bottom+0.68):
    ring("Brass", (gx, gy, z), 0.36, 0.013, "XY", 48)
for i in range(28):
    t = i*math.tau/28
    points = [(gx+0.36*math.cos(t), gy+0.36*math.sin(t), bottom),
              (gx+0.36*math.cos(t), gy+0.36*math.sin(t), bottom+0.68)]
    for j in range(1, 9):
        a = j*math.pi/16
        points.append((gx+0.36*math.cos(a)*math.cos(t),
                       gy+0.36*math.cos(a)*math.sin(t), bottom+0.68+0.35*math.sin(a)))
    tube("Brass", points, 0.006, 5)
ring("Brass", (gx, gy, bottom+1.12), 0.072, 0.012, "XZ", 24)

GROUP = "Furniture"
for y in (7.0, 18.0, 29.0, 42.0, 53.0):
    for i in range(5):
        box("Wood", (4.02+i*0.10, y, 1.21), (0.075, 1.85, 0.06))
        box("Wood", (4.48, y, 1.47+i*0.105), (0.065, 1.85, 0.075))
    for dy in (-0.72, 0.72):
        for x in (4.05, 4.48):
            tube("Iron", [(x, y+dy, 0.73), (x+0.05, y+dy, 1.12),
                          (x, y+dy, 1.25)], 0.035)
        tube("Iron", [(3.99, y+dy, 1.23), (3.94, y+dy, 1.5),
                      (4.14, y+dy, 1.59), (4.48, y+dy, 1.5)], 0.035)
    suitcase(4.22, y+1.52, 0.73, 0.48, 0.45, 0.68, "DarkLeather")

GROUP = "Signs"
for x, y, z, radius in ((3.58, 2.10, 4.45, 0.64), (4.0, 25.0, 4.1, 0.38)):
    cylinder("Cream", (x, y-0.05, z), (x, y+0.06, z), radius, 80)
    ring("BlackSteel", (x, y-0.075, z), radius, 0.025, "XZ")
    ring("Brass", (x, y-0.080, z), radius-0.04, 0.006, "XZ")
    for t in [i*math.tau/12 for i in range(12)]:
        rivet("BlackSteel", (x+(radius-0.065)*math.cos(t), y-0.08,
                             z+(radius-0.065)*math.sin(t)), radius=0.012)
    text("9", (x-radius*0.28, y-0.084, z-0.035), radius*1.50, "Lettering")
    text("3", (x+radius*0.42, y-0.084, z+radius*0.31), radius*0.62, "Lettering")
    text("4", (x+radius*0.42, y-0.084, z-radius*0.33), radius*0.62, "Lettering")
    box("Lettering", (x+radius*0.42, y-0.089, z+0.01), (radius*0.51, 0.007, 0.020))
    tube("Iron", [(x-0.2, y, z+radius), (x-0.2, y, z+radius+0.32),
                  (4.64, y, z+radius+0.32)], 0.033)
    tube("Iron", [(4.64, y, z+radius+0.32), (4.64, y, z+0.1),
                  (x+0.5, y, z+radius+0.25)], 0.031)
    ring("Iron", (4.32, y, z+radius+0.13), 0.20, 0.022, "XZ", 40)

GROUP = "Lanterns"
lamps = []
for y in (-2.5, 7.5, 17.5, 27.5, 37.5, 47.5, 57.5):
    x, z = 4.22, 4.55
    tube("Iron", [(4.67, y, 4.4), (4.35, y, 4.9), (x, y, 4.9)], 0.032)
    box("Lamp", (x, y, z), (0.20, 0.20, 0.37))
    for dx in (-0.15, 0.15):
        for dy in (-0.15, 0.15):
            cylinder("BlackSteel", (x+dx, y+dy, z-0.24),
                     (x+dx*0.8, y+dy*0.8, z+0.23), 0.017, 8)
    box("BlackSteel", (x, y, z-0.25), (0.33, 0.33, 0.07))
    cylinder("BlackSteel", (x, y, z+0.22), (x, y, z+0.41), 0.28, 4, 0.05)
    lamps.append([x-0.23, y-0.12, z])

GROUP = "Puddles"
for x, y, rx, ry in [(1.6, -0.8, 0.55, 0.40), (0.4, 3.2, 0.27, 1.2),
                      (1.6, 6.2, 0.60, 0.24), (0.5, 11, 0.4, 1.1),
                      (1.0, 17, 0.60, 1.4), (1.9, 27, 0.30, 2.2),
                      (0.25, 33, 0.50, 3)]:
    face("Puddle", [(x+rx*math.cos(t)*(1+random.uniform(-0.13, 0.13)),
                     y+ry*math.sin(t)*(1+random.uniform(-0.13, 0.13)), 0.702)
                    for t in [i*math.tau/32 for i in range(32)]])

objects = defaultdict(list)
for (group, material), data in meshes.items():
    mesh = bpy.data.meshes.new(f"{group}_{material}")
    mesh.from_pydata(data["verts"], [], data["faces"])
    mesh.materials.append(MATERIALS[material])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for i, coordinate in enumerate(data["uv"]):
        uv.data[i].uv = coordinate
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(obj)
    objects[group].append(obj)
    if material not in ("Glass", "Puddle", "Gravel", "Lettering"):
        bevel = obj.modifiers.new("Machined and worn edges", "BEVEL")
        bevel.width = 0.009 if group not in ("Architecture", "Track") else 0.015
        bevel.segments = 2
        bevel.limit_method = "ANGLE"
        bevel.angle_limit = 0.60
    if material not in ("Brick", "Stone", "Glass"):
        for polygon in mesh.polygons:
            polygon.use_smooth = len(polygon.vertices) == 4

manifest = {
    "materials": {k: {"color": v[0], "metallic": v[1], "roughness": v[2],
                       "texture": v[3]} for k, v in PALETTE.items()},
    "meshes": [],
    "camera": {"position": [2.5, -5.8, 2.35], "target": [-3.5, 30, 2.4], "fov": 70},
    "lamps": lamps,
    "chimney": [TX, 4.2, 4.62],
}
for group, group_objects in objects.items():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in group_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = group_objects[0]
    path = OUT / f"{group}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y", axis_up="Z", bake_space_transform=False,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_triangles=True,
        path_mode="RELATIVE", add_leaf_bones=False,
    )
    if path.stat().st_size < 1024:
        raise RuntimeError(f"Empty mesh export: {path}")
    coordinates = [o.matrix_world @ v.co for o in group_objects for v in o.data.vertices]
    manifest["meshes"].append({
        "name": group, "file": str(path.relative_to(ROOT)),
        "vertices": sum(len(o.data.vertices) for o in group_objects),
        "material_slots": sorted({m.name for o in group_objects for m in o.data.materials}),
        "source_bounds_m": {
            "minimum": [min(p[i] for p in coordinates) for i in range(3)],
            "maximum": [max(p[i] for p in coordinates) for i in range(3)],
        },
    })

bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "HiddenPlatform.blend"))
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
(ROOT / "Art/Models/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("PLATFORM_MODEL_OK", json.dumps({
    "groups": len(objects),
    "vertices": sum(len(o.data.vertices) for group in objects.values() for o in group),
    "manifest": str(OUT / "manifest.json"),
}))
