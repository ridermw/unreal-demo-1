"""Build the authored railway diorama in Blender and export material-aware FBX groups."""

import json
import math
import random
from collections import defaultdict
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Art" / "Models" / "Refined"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(934)
CAMERA = {"position": [2.5, -5.8, 2.35], "target": [-2.55, 30, 1.72], "fov": 70}
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

PALETTE = {
    "Brick": ((0.28, 0.105, 0.055), 0.0, 0.87, "brick", 1.4),
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
    "Interior": ((0.30, 0.18, 0.07), 0.0, 0.85, "wood", 2.0),
    "SignFace": ((0.55, 0.42, 0.25), 0.0, 0.72, "sign_face", 1.0),
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


def camera_pixel_on_plane(pixel, plane_y, slope=0):
    position = Vector(CAMERA["position"])
    forward = (Vector(CAMERA["target"])-position).normalized()
    right = forward.cross(Vector((0,0,1))).normalized()
    up = right.cross(forward).normalized()
    tangent = math.tan(math.radians(CAMERA["fov"])/2)
    ray = forward + right*((pixel[0]/1536*2-1)*tangent)
    ray += up*((1-pixel[1]/864*2)*tangent*864/1536)
    distance = (plane_y+slope*3.6-position.y-slope*position.x)/(ray.y+slope*ray.x)
    return position + ray*distance


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
for side in (4.95,):
    GROUP = "Windows"
    inward = -1 if side > 0 else 1
    box("Interior",(side-inward*1.4,28,3.7),(.22,80,7.4))
    GROUP = "Architecture"
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
        box("Interior",(side-inward*1.1,y+2.5,3.5),(.12,2.0,3.6))
        for zz in (2.0,3.05,4.1):
            box("Wood",(side-inward*.7,y+2.5,zz),(.65,1.9,.09))
        box("Lamp",(side-inward*.45,y+2.5,4.5),(.15,.13,.2))
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

left_lamps = []
GROUP="Windows"
box("Interior",(-11.2,28,4.1),(.18,80,8.2))
GROUP="Architecture"
for y in range(-8, 68, 5):
    side, center = -9.8, y+2.5
    box("Brick", (side,y,3.85),(.65,.82,6.5))
    box("Stone", (side+.10,y,.89),(.85,1.05,.36))
    box("Stone", (side+.1,y,4.0),(.80,1.02,.28))
    box("Brick", (side,center,.97),(.5,4.2,.7))
    box("Brick", (side,center,3.7),(.5,4.2,1.08))
    box("Brick", (side,center,6.94),(.5,4.2,.55))
    for z,width,height in ((.68,.76,.15),(3.65,.72,.13),(3.95,.84,.12),
                           (4.15,.76,.13),(6.78,.75,.12),(7.05,.90,.17)):
        box("Stone",(side+.12,center,z),(width,5.0,height))
    for offset in (-1.6,1.6):
        box("Brick",(side,center+offset,2.25),(.50,1.04,2.0))
        box("Brick",(side,center+offset,5.37),(.50,1.04,2.65))
    for base,spring,radius in ((1.18,2.73,.92),(4.35,5.72,1.05)):
        front=side+.35
        for edge in (-1,1):
            box("Stone",(front,center+edge*(radius+.08),(base+spring)/2),
                (.22,.14,spring-base))
        box("Stone",(front,center,base-.08),(.42,2*radius+.34,.18))
        for j in range(20):
            a,b=j*math.pi/20+.004,(j+1)*math.pi/20-.004
            points=[(front+.12,center+r*math.cos(t),spring+r*math.sin(t))
                    for r,t in ((radius,a),(radius,b),(radius+.19,b),(radius+.19,a))]
            face("Brick",list(reversed(points)))
            middle=(a+b)/2
            top=spring+radius*math.sin(middle)
            ceiling=3.33 if base<2 else 6.82
            if ceiling>top:
                box("Brick",(side,center+radius*math.cos(middle),(ceiling+top)/2),
                    (.5,.18,ceiling-top))
        GROUP="Windows"
        box("AmberGlass",(front-.10,center,(base+spring)/2),(.035,2*radius,spring-base))
        face("AmberGlass",[(front-.10,center,spring)]+[
            (front-.10,center+radius*math.cos(t),spring+radius*math.sin(t))
            for t in [j*math.pi/32 for j in range(33)]])
        box("Interior",(side-.95,center,(base+spring)/2),(.12,2*radius,spring-base+1.0))
        for offset in (-radius,-radius/2,0,radius/2,radius):
            top=spring+math.sqrt(max(0,radius**2-offset**2))
            box("Iron",(front+.035,center+offset,(base+top)/2),(.08,.04,top-base))
        for z in (base+.52,spring-.18,spring):
            box("Iron",(front+.055,center,z),(.10,2*radius,.05))
        GROUP="Architecture"
    for j in range(8):
        yy=y+.4+j*.60
        GROUP="Furniture"
        cylinder("Iron",(-7.0,yy,.66),(-7.0,yy,1.64),.016,8)
        cylinder("Brass",(-7.0,yy,1.64),(-7.0,yy,1.71),.024,8,.008)
    for z in (.94,1.58):
        cylinder("Iron",(-7.0,y,.0+z),(-7.0,y+5,z),.024,10)
    GROUP="Lanterns"
    x,z=-9.16,3.37
    tube("Iron",[(side+.30,center,3.5),(x,center,3.67),(x,center,3.45)],.024,8)
    box("Lamp",(x,center,z),(.13,.15,.25))
    for yy in (-.1,.1):
        for xx in (-.1,.1):
            cylinder("Iron",(x+xx,center+yy,z-.17),(x+xx,center+yy,z+.17),.011,8)
    cylinder("Iron",(x,center,z+.17),(x,center,z+.29),.18,4,.03)
    left_lamps.append([x+.10,center,z])
    GROUP="Architecture"

GROUP = "Roof"
for y in range(-3,68,10):
    x=-7.1
    cylinder("Iron",(x,y,.65),(x,y,6.75),.13,16,.085)
    for z,radius in ((.8,.27),(1.05,.21),(5.8,.20),(6.0,.28),(6.2,.34)):
        cylinder("Iron",(x,y,z-.07),(x,y,z+.07),radius,12)
    for dx,dy in ((-2.4,0),(2.4,0),(0,-2.4),(0,2.4)):
        tube("Iron",[(x,y,5.8),(x+dx*.3,y+dy*.3,6.6),
                     (x+dx*.7,y+dy*.7,7.12),(x+dx,y+dy,7.4)],.066,10)
        tube("Iron",[(x,y,6.15),(x+dx*.45,y+dy*.45,6.85),
                     (x+dx,y+dy,7.4)],.032,8)
    for r,z in ((.30,6.28),(.23,6.40),(.16,6.5)):
        ring("Brass",(x,y,z),r,.015,"XY",32)
for y in range(-8, 70, 5):
    arch("Iron", y, 6.65, 7.4, 5.2, 0.10, -2.55)
    arch("Iron", y, 6.65, 7.4, 4.15, 0.065, -2.55)
    for depth in (-.10,.10):
        arch("Iron",y+depth,6.65,7.4,5.2,.075,-2.55)
        arch("Iron",y+depth,6.65,7.4,4.15,.055,-2.55)
    for i in range(17):
        t = (i+0.5)*math.pi/17
        p = (-2.55+7.4*math.cos(t), y, 6.65+5.2*math.sin(t))
        t2 = (i+1)*math.pi/17
        q = (-2.55+7.4*math.cos(t2), y, 6.65+4.15*math.sin(t2))
        tube("Iron", [p, q], 0.035, 6)
        p2 = (-2.55+7.4*math.cos(t), y, 6.65+4.15*math.sin(t))
        q2 = (-2.55+7.4*math.cos(t2), y, 6.65+5.2*math.sin(t2))
        tube("Iron", [p2, q2], 0.026, 6)
    for x in (-9.65, 4.55):
        box("Iron", (x, y, 3.7), (0.18, 0.26, 6.0))
        box("Iron", (x, y, 0.90), (0.43, 0.46, 0.40))
        box("Brass", (x, y, 6.5), (0.38, 0.43, 0.16))
        for s in (-1, 1):
            tube("Iron", [(x, y, 5.4), (x, y+s*1.2, 6.55)], 0.07)
            for radius in (.28, .46):
                ring("Iron", (x, y+s*.5, 6.1), radius, .018, "YZ", 32)
        for z, width in ((5.95, .3), (6.18, .43), (6.42, .6)):
            box("Iron", (x, y, z), (width, .36, .10))
    for i in range(20):
        a, b = i*math.pi/20, (i+1)*math.pi/20
        pts = [(-2.55+7.4*math.cos(t), yy, 6.65+5.2*math.sin(t))
               for t, yy in ((a, y), (b, y), (b, y+5), (a, y+5))]
        face("Glass" if 6 <= i <= 13 else "RoofPanel", pts)
        if i in (4, 7, 12, 15):
            x = -2.55+7.4*math.cos(a)
            z = 6.65+5.2*math.sin(a)-.18
            tube("Iron", [(x, y, z), (x-.12, y+2.5, z-.32), (x, y+5, z)], .025, 6)
    for offset in (1.25, 2.5, 3.75):
        arch("Iron", y+offset, 6.65, 7.4, 5.2, 0.025, -2.55)
for i in range(21):
    t = i*math.pi/20
    cylinder("Iron", (-2.55+7.4*math.cos(t), -8, 6.65+5.2*math.sin(t)),
             (-2.55+7.4*math.cos(t), 72, 6.65+5.2*math.sin(t)), 0.045, 8)

GROUP = "FarWall"
for x in (-9.7,4.65):
    box("Brick",(x,66,3.1),(.85,1.0,5.8))
for x in [i*.65-9.65 for i in range(23)]:
    top=6.65+5.2*math.sqrt(max(0,1-((x+2.55)/7.4)**2))
    box("Iron",(x,66,(4.9+top)/2),(.06,.16,top-4.9))
box("Iron",(-2.55,66,4.95),(14.8,.35,.32))
for z in (6.2,7.8,9.4):
    width=14.8 if z<6.65 else 14.8*math.sqrt(max(0,1-((z-6.65)/5.2)**2))
    box("Iron",(-2.55,66,z),(width,.16,.06))
for i in range(32):
    a,b=i*math.pi/32,(i+1)*math.pi/32
    face("Glass",[(-2.55+7.4*math.cos(a),66.1,4.95),
                  (-2.55+7.4*math.cos(b),66.1,4.95),
                  (-2.55+7.4*math.cos(b),66.1,6.65+5.2*math.sin(b)),
                  (-2.55+7.4*math.cos(a),66.1,6.65+5.2*math.sin(a))])
for y in (70,78,88,100):
    for x in (-7.8,3.0):
        box("Brick",(x,y,3.0),(.5,.5,5.8))
        box("Stone",(x,y,5.5),(.75,.75,.2))
    box("Iron",(-2.4,y,5.75),(11.3,.18,.18))
for x in (-9.8,4.6):
    box("Brick",(x,71,4.0),(.8,13,7.8))
box("Stone",(0,74,.3),(9,22,.6))

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
for side in (-1, 1):
    box("BlackSteel", (TX+side*1.16, 8.15, 1.64), (.40, 9.6, .09))
    box("Scarlet", (TX+side*1.36, 8.15, 1.52), (.045, 9.6, .20))
box("BlackSteel",(TX,2.80,1.55),(2.65,2.35,.08))
cylinder("Scarlet", (TX, 4.35, 2.80), (TX, 11.75, 2.80), 1.02, 80)
cylinder("BlackSteel", (TX, 3.15, 2.80), (TX, 4.50, 2.80), 1.065, 80)
cylinder("BlackSteel", (TX, 3.02, 2.80), (TX, 3.16, 2.80), 0.985, 80)
ring("BlackSteel", (TX, 2.98, 2.80), 0.985, 0.055)
ring("Brass", (TX, 2.965, 2.80), 1.018, 0.012)
for row in range(12):
    r0, r1 = row*.985/12, (row+1)*.985/12
    for segment in range(96):
        a, b = segment*math.tau/96, (segment+1)*math.tau/96
        points=[]
        for radius, theta in ((r0,a),(r1,a),(r1,b),(r0,b)):
            depth=3.012-.13*math.sqrt(max(0,1-(radius/.985)**2))
            points.append((TX+radius*math.cos(theta),depth,2.8+radius*math.sin(theta)))
        if row == 0:
            points=points[:3]
        face("BlackSteel",points)
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
box("Scarlet", (TX, 1.87, 1.12), (2.9, 0.28, 0.54))
for x in (TX-1.06, TX+1.06):
    cylinder("BlackSteel", (x, 1.80, 1.12), (x, 1.34, 1.12), 0.15, 24)
    cylinder("BlackSteel", (x, 1.34, 1.12), (x, 1.20, 1.12), 0.25, 40)
    ring("BlackSteel", (x, 1.33, 1.12), 0.16, 0.030)
for row in (.90, 1.32):
    for i in range(13):
        rivet("BlackSteel", (TX-1.28+i*0.21, 1.71, row), radius=0.025)
tube("BlackSteel", [(TX, 1.45, 1.15), (TX, .85, 0.70), (TX+0.10, 1.0, 0.42)], 0.053)
tube("BlackSteel", [(TX-0.45, 1.43, 1.3), (TX-0.4, 1.05, 0.63),
                    (TX-0.25, .92, 0.45)], 0.044)
cylinder("Brass", (TX, 2.91, 2.8), (TX, 2.73, 2.8), 0.08, 24)
cylinder("BlackSteel", (TX-.32, 2.72, 2.8), (TX+.30, 2.72, 2.8), .029, 16)
tube("BlackSteel", [(TX,2.72,2.9),(TX,2.7,2.64),(TX+.06,2.68,2.57)], .031, 16)
for z in (2.3, 3.3):
    box("BlackSteel", (TX+0.65, 2.90, z), (0.4, 0.07, 0.065))
text("5979", (TX, 2.913, 2.23), 0.12, "Brass")
# Tall apron, coupling links, door hardware and fittings make the hero silhouette mechanical.
face("BlackSteel", [(TX-1.30,1.74,1.38),(TX+1.30,1.74,1.38),
                    (TX+1.12,3.08,1.96),(TX-1.12,3.08,1.96)])
for x in (-.94,-.62,-.3,0,.3,.62,.94):
    rivet("BlackSteel",(TX+x,1.75,1.42),radius=.018)
for index in range(7):
    ring("BlackSteel", (TX+.015*index,.87+.035*index,.74-index*.065),
         .073,.018,"XZ" if index%2 else "YZ",20)
for x in (TX-.60,TX+.65):
    tube("BlackSteel",[(x,1.38,1.33),(x-.06,.90,.86),(x+.10,.87,.46)],.042,14)
    for j in range(10):
        ring("BlackSteel",(x,1.0,.62+j*.04),.05,.012,"XY",12)
box("Brass",(TX,2.97,3.87),(.18,.15,.27))
cylinder("Brass",(TX,2.9,3.92),(TX,2.80,3.92),.087,32)
cylinder("Cream",(TX,2.79,3.92),(TX,2.78,3.92),.065,32)
ring("Brass",(TX,2.90,4.08),.068,.012,"XZ",24)
for y in (4.6,5.6,7.8,9.7,10.9):
    for side in (-1,1):
        xx=TX+side*.85
        cylinder("BlackSteel",(xx,y,3.34),(xx,y,3.50),.025,12)
        ring("Brass",(xx,y,3.43),.049,.009,"XZ",20)
for side in (-1,1):
    xx=TX+side*1.08
    for offset in (0,.10):
        tube("Brass",[(xx,4.7,2.40+offset),(xx,6.4,2.35+offset),
                       (xx,8.6,2.25+offset),(xx,10.7,2.1+offset)],.024,12)
    for y in (5.2,7.2,9.2):
        for z in (2.0,3.25):
            box("BlackSteel",(xx,y,z),(.06,.13,.07))
for y in (6.6,9.2):
    cylinder("Brass",(TX+.44,y,3.62),(TX+.44,y,4.12),.057,18)
    ring("Brass",(TX+.44,y,4.16),.10,.012,"XY",24)

GROUP = "Wheels"
for y, radius in ((3.75, 0.48), (5.5, 0.92), (7.45, 0.92), (9.4, 0.92), (11.75, 0.5)):
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
    for y in (5.5,7.45,9.4):
        for j in range(5):
            points=[(TX+side*1.06,y+.58*math.cos(t),1.52+j*.032+.10*math.sin(t))
                    for t in [i*math.pi/12 for i in range(13)]]
            tube("BlackSteel",points,.022,6)
        arc=[(TX+side*1.15,y+.93*math.cos(t),1.0+.93*math.sin(t))
             for t in [i*math.pi/32 for i in range(33)]]
        tube("Scarlet",arc,.07,10)

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
cx, cy = 4.12, -2.0
box("Wood", (cx, cy, 1.03), (1.45, 1.12, 0.12))
for side in (-1, 1):
    for yy in (cy-0.38, cy+0.38):
        ring("BlackSteel", (cx+side*0.60, yy, 0.9), 0.20, 0.043, "YZ", 24)
    tube("Brass", [(cx+side*0.63, cy+0.42, 1.03), (cx+side*0.63, cy+0.42, 2.14),
                   (cx+side*0.51, cy+0.42, 2.36), (cx, cy+0.42, 2.40)], 0.030)
suitcase(cx, cy-0.12, 1.09, 1.27, 0.86, 0.41)
suitcase(cx+0.19, cy+0.10, 1.51, 0.75, 0.59, 0.23, "DarkLeather")
suitcase(3.12, 3.00, 0.73, 0.64, 0.36, 0.86)
suitcase(3.86, 3.45, 0.73, 0.79, 0.43, 1.15, "DarkLeather")
for layer in range(4):
    for i in range(30):
        for j in range(18):
            pts=[]
            for ii,jj in ((i,j),(i+1,j),(i+1,j+1),(i,j+1)):
                u,v=ii/30,jj/18
                x=cx+.12+u*.65
                y=cy-.55+v*.75
                z=1.76+layer*.034+.017*math.sin(u*math.pi*6+layer*.5)+.012*math.sin(v*math.pi*4)
                if v<.16:
                    z-=.38*(1-v/.16)
                    y=cy-.53-.016*layer
                pts.append((x,y,z))
            face("Blanket",pts)
for i in range(22):
    cylinder("Blanket", (cx+.12+i*.031,cy-.55,1.40),
             (cx+.12+i*.031,cy-.56,1.30-random.random()*.08),.006,5)
# Delicate cage bars and domed crown remain actual geometry.
gx, gy, bottom = cx-.35, cy+0.14, 1.52
for z in (bottom, bottom+0.06, bottom+0.34, bottom+0.47):
    ring("Brass", (gx, gy, z), 0.29, 0.009, "XY", 48)
cylinder("Brass",(gx,gy,bottom-.02),(gx,gy,bottom+.035),.292,64)
for i in range(40):
    t = i*math.tau/40
    points = [(gx+0.29*math.cos(t), gy+0.29*math.sin(t), bottom),
              (gx+0.29*math.cos(t), gy+0.29*math.sin(t), bottom+0.47)]
    for j in range(1, 9):
        a = j*math.pi/16
        points.append((gx+0.29*math.cos(a)*math.cos(t),
                       gy+0.29*math.cos(a)*math.sin(t), bottom+0.47+0.24*math.sin(a)))
    tube("Brass", points, 0.0045, 6)
ring("Brass", (gx, gy, bottom+.78), 0.05, 0.009, "XZ", 24)

GROUP = "Furniture"
for y in (3.8, 15.0, 27.0, 42.0, 53.0):
    for i in range(5):
        box("Wood", (4.02+i*0.10, y, 1.21), (0.075, 1.85, 0.06))
        box("Wood", (4.48, y, 1.55+i*0.14), (0.065, 1.85, 0.10))
    for dy in (-0.72, 0.72):
        for x in (4.05, 4.48):
            tube("Iron", [(x, y+dy, 0.73), (x+0.05, y+dy, 1.12),
                          (x, y+dy, 1.25)], 0.035)
        tube("Iron", [(3.99, y+dy, 1.23), (3.94, y+dy, 1.5),
                      (4.14, y+dy, 1.59), (4.48, y+dy, 1.5)], 0.035)
    suitcase(4.22, y+1.52, 0.73, 0.48, 0.45, 0.68, "DarkLeather")

GROUP = "Signs"
for x, y, z, radius in ((3.58, 2.10, 4.10, 0.48), (4.0, 25.0, 4.1, 0.38)):
    cylinder("Cream", (x, y-0.05, z), (x, y+0.06, z), radius, 80)
    ring("BlackSteel", (x,y+.065,z),radius,.008,"XZ")
    ring("Iron", (x, y-0.075, z), radius, 0.010, "XZ")
    ring("Brass", (x, y-0.080, z), radius-0.012, 0.003, "XZ")
    for i in range(96):
        a,b=i*math.tau/96,(i+1)*math.tau/96
        face("SignFace",[(x,y-.090,z),
                        (x+radius*.985*math.cos(a),y-.090,z+radius*.985*math.sin(a)),
                        (x+radius*.985*math.cos(b),y-.090,z+radius*.985*math.sin(b))],
             [(.5,.5),(.5+.5*math.cos(a),.5+.5*math.sin(a)),
              (.5+.5*math.cos(b),.5+.5*math.sin(b))])
    # Retain lettering as real embossed back-face detail, hidden from the target view.
    text("9", (x, y+.065, z), radius*1.4, "Lettering", rotation=(math.pi/2,0,math.pi))
    if y < 3:
        def screen_tube(material, pixels, thickness):
            tube(material,[camera_pixel_on_plane(p,y,.60) for p in pixels],thickness,12)
        screen_tube("Iron",[(1084,48),(1263,47)],.017)
        screen_tube("Iron",[(1263,39),(1263,192)],.021)
        screen_tube("Iron",[(1085,48),(1106,62),(1132,76),(1160,91),
                            (1187,107),(1210,123),(1231,144),(1249,169),(1256,187)],.016)
        screen_tube("Iron",[(1086,46),(1087,85)],.015)
        for cx,cy,radius_px,start,turns in ((1169,71,15,-math.pi/2,1.12),
                                           (1225,87,37,-math.pi/2,1.32),
                                           (1246,133,12,-math.pi/2,1.40),
                                           (1118,57,5,math.pi,1.1)):
            pixels=[]
            for j in range(97):
                t=start+j*math.tau*turns/96
                rr=radius_px*(1-.73*max(0,(j/96-.58)/.42))
                pixels.append((cx+rr*math.cos(t),cy+rr*math.sin(t)))
            screen_tube("Iron",pixels,.019 if radius_px>20 else .015)
        pixels=[(1075+7*math.cos(t),57+10*math.sin(t))
                for t in [j*math.tau/64 for j in range(65)]]
        screen_tube("Brass",pixels,.008)
        screen_tube("Brass",[(1086,45),(1087,28),(1089,24)],.014)
        anchor=camera_pixel_on_plane((1264,114),y,.60)
        box("Iron",anchor,(.055,.13,1.15))
        boss=camera_pixel_on_plane((1220,91),y,.60)
        box("BlackSteel",boss,(.20,.10,.23))
        cylinder("BlackSteel",boss+Vector((.08,-.06,0)),boss+Vector((.08,-.13,0)),.09,48)
        ring("Iron",boss+Vector((.08,-.14,0)),.085,.010,"XZ",48)
        cylinder("Brass",boss+Vector((.08,-.13,0)),boss+Vector((.08,-.15,0)),.018,20)
        cylinder("BlackSteel",boss+Vector((0,0,-.10)),boss+Vector((0,0,-.26)),.045,20,.027)
    else:
        top=z+radius+.26
        tube("Iron",[(x,y,z+radius),(x,y,top),(4.66,y,top)],.018,10)
        tube("Iron",[(x,y,top),(4.66,y,top-.55)],.014,10)

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
lamps.extend(left_lamps)

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
    if group == "Locomotive":
        data["verts"] = [Vector((v.x, v.y, v.z*1.13+.15))
                         for v in data["verts"]]
    elif group in ("CabTender", "Carriages"):
        data["verts"] = [Vector((v.x,v.y,v.z+.3 if v.z>1.8 else v.z)) for v in data["verts"]]
    mesh = bpy.data.meshes.new(f"{group}_{material}")
    mesh.from_pydata(data["verts"], [], data["faces"])
    mesh.materials.append(MATERIALS[material])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for i, coordinate in enumerate(data["uv"]):
        uv.data[i].uv = coordinate
    if material not in ("Glass", "Puddle", "Gravel", "Lettering", "Blanket"):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00005)
        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                edge.smooth = edge.calc_face_angle() < .55
        bm.to_mesh(mesh)
        bm.free()
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.collection.objects.link(obj)
    objects[group].append(obj)
    if group not in ("Roof", "Track", "Signs") and material not in ("Glass", "Puddle", "Gravel", "Lettering", "Blanket"):
        bevel = obj.modifiers.new("Machined and worn edges", "BEVEL")
        bevel.width = (0.032 if group == "Luggage" and material in ("Leather","DarkLeather")
                       else .012 if group == "Furniture" and material == "Wood" else .008)
        bevel.segments = 3
        bevel.limit_method = "ANGLE"
        bevel.angle_limit = 0.60
    if material not in ("Brick", "Stone", "Glass"):
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        normals = obj.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        normals.keep_sharp = True

manifest = {
    "materials": {k: {"color": v[0], "metallic": v[1], "roughness": v[2],
                       "texture": v[3]} for k, v in PALETTE.items()},
    "meshes": [],
    "camera": CAMERA,
    "lamps": lamps,
    "chimney": [TX, 4.2, 5.37],
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
    exported_triangles = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in group_objects:
        evaluated = obj.evaluated_get(depsgraph)
        evaluated_mesh = evaluated.to_mesh()
        evaluated_mesh.calc_loop_triangles()
        exported_triangles += len(evaluated_mesh.loop_triangles)
        evaluated.to_mesh_clear()
    manifest["meshes"].append({
        "name": group, "file": str(path.relative_to(ROOT)),
        "vertices": sum(len(o.data.vertices) for o in group_objects),
        "exported_triangles": exported_triangles,
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
