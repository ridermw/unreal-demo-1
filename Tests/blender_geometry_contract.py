"""Read-only tests of the actual swept-tube function inside Blender's Python."""

import ast
from collections import Counter
import math
from pathlib import Path
import unittest

from mathutils import Vector
import bpy


ROOT = Path(__file__).resolve().parents[1]
source = ast.parse((ROOT / "Scripts/build_station.py").read_text())
definition = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "tube")
namespace = {"Vector": Vector, "math": math, "PALETTE": {"Test": (None, None, None, None, 1)}}
exec(compile(ast.Module(body=[definition], type_ignores=[]), "build_station.tube", "exec"), namespace)


class SweptTubeTests(unittest.TestCase):
    def setUp(self):
        self.faces = []
        namespace["face"] = lambda material, points, uv=None: self.faces.append([tuple(p) for p in points])

    def assert_closed(self):
        edges = Counter()
        for face in self.faces:
            vertices = [tuple(round(c, 6) for c in p) for p in face]
            for a, b in zip(vertices, vertices[1:] + vertices[:1]):
                self.assertNotEqual(a, b)
                edges[tuple(sorted((a, b)))] += 1
        self.assertTrue(edges)
        self.assertTrue(all(count == 2 for count in edges.values()))

    def test_open_bent_path_has_only_two_end_caps(self):
        namespace["tube"]("Test", [(0, 0, 0), (0, 0, 1), (1, 0, 2)], .1, 8)
        self.assertEqual(len(self.faces), 18)
        self.assertEqual(sum(len(face) == 8 for face in self.faces), 2)
        self.assert_closed()

    def test_ring_is_continuous_and_has_no_segment_caps(self):
        points = [(math.cos(i * math.tau / 8), math.sin(i * math.tau / 8), 0) for i in range(9)]
        namespace["tube"]("Test", points, .1, 8)
        self.assertEqual(len(self.faces), 64)
        self.assertTrue(all(len(face) == 4 for face in self.faces))
        self.assert_closed()

    def test_side_faces_point_outward(self):
        namespace["tube"]("Test", [(0, 0, 0), (0, 0, 1)], .1, 8)
        for face in self.faces[:8]:
            a, b, c = map(Vector, face[:3])
            normal = (b - a).cross(c - a)
            center = sum((Vector(p) for p in face), Vector()) / 4
            self.assertGreater(normal.dot(Vector((center.x, center.y, 0))), 0)

    def test_invalid_paths_raise(self):
        for points in ([(0, 0, 0)], [(0, 0, 0), (0, 0, 0)]):
            with self.assertRaises(ValueError):
                namespace["tube"]("Test", points, .1, 8)

    def test_saved_blanket_has_consistent_shared_edge_winding(self):
        with bpy.data.libraries.load(str(ROOT/"Art/Models/Refined/HiddenPlatform.blend"),link=False) as (_,data):
            data.meshes=["Luggage_Blanket"]
        mesh=data.meshes[0]
        self.assertIsNotNone(mesh)
        directions={}
        for polygon in mesh.polygons:
            vertices=list(polygon.vertices)
            for a,b in zip(vertices,vertices[1:]+vertices[:1]):
                directions.setdefault(tuple(sorted((a,b))),[]).append((a,b))
        inconsistent=[edge for edge,pairs in directions.items() if len(pairs)==2 and pairs[0]==pairs[1]]
        self.assertEqual(inconsistent,[])


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SweptTubeTests))
if not result.wasSuccessful():
    raise RuntimeError("Swept tube geometry contracts failed")
print("BLENDER_GEOMETRY_CONTRACTS_OK")
