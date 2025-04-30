# SPDX-FileCopyrightText: 2025 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import traceback

import addon_utils
import bpy
from bpy.types import Collection, Object


def _add_move_to_collection(name: str, obs: list[Object]) -> Collection:
    coll = bpy.data.collections.new(name)
    bpy.context.collection.children.link(coll)
    for ob in obs:
        bpy.context.collection.objects.unlink(ob)
        coll.objects.link(ob)
    return coll


def _add_curve(name: str, radius=1.0, order=5, resolution=64) -> Object:
    bpy.ops.curve.primitive_nurbs_path_add()
    ob = bpy.context.object
    ob.name = name
    ob.data.resolution_u = resolution
    spline = ob.data.splines[0]
    spline.order_u = order
    for p in spline.points:
        p.radius = radius
    return ob


def _add_mesh(name: str, location=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)) -> Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    return ob


def test_101() -> None:
    _add_mesh("Object Scale", scale=(1.5, 1.0, 1.0))


def test_102() -> None:
    ob = _add_mesh("Empty Mesh")
    ob.data.clear_geometry()


def test_201() -> None:
    ob = _add_mesh("Wrong Mod Order")
    ob.modifiers.new("Curve", "CURVE")
    ob.modifiers.new("Subd", "SUBSURF")


def test_202() -> None:
    a = _add_mesh("AB", location=(0.0, 0.0, 1.0), scale=(0.5, 0.5, 0.5))
    b = _add_mesh("BA")
    a.modifiers.new("Project", "SHRINKWRAP").target = b
    b.modifiers.new("Bool", "BOOLEAN").object = a
    _add_move_to_collection("Cyclic Dependency", (a, b))


def test_301() -> None:
    curve = _add_curve("Radius", radius=1.5)
    mesh = _add_mesh("Radius Deform")
    mesh.modifiers.new("Curve", "CURVE").object = curve
    _add_move_to_collection("Curve Radius", (curve, mesh))


def test_302() -> None:
    _add_curve("Low Order", order=3)


def test_303() -> None:
    curve = _add_curve("Low Resolution", resolution=12)
    mesh = _add_mesh("Resolution Deform")
    mesh.modifiers.new("Curve", "CURVE").object = curve
    _add_move_to_collection("Curve Resolution", (curve, mesh))


def test_401() -> None:
    bpy.context.collection.name = "Collection All Problems"


def main() -> None:
    coll = bpy.data.collections.new("Sidekick")
    bpy.context.scene.collection.children.link(coll)
    view_layer = bpy.context.view_layer
    view_layer.active_layer_collection = view_layer.layer_collection.children[-1]

    for name, func in globals().items():
        if name.startswith("test"):
            func()

    for ext_id in addon_utils.modules().mapping:
        if ext_id.split(".")[-1] == "sidekick":
            addon_utils.enable(ext_id, default_set=True)
            break
    else:
        raise RuntimeError("Extension not found")

    test_problems = {int(x.split("_")[1]) for x in globals().keys() if x.startswith("test")}
    scene_problems = {x.code for x in bpy.context.window_manager.sidekick.problems(rescan=True)}
    if (result := test_problems - scene_problems):
        raise Exception(result)


try:
    main()
except:
    traceback.print_exc()
    sys.exit(1)
