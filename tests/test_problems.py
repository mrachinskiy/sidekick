# SPDX-FileCopyrightText: 2025 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import traceback

import addon_utils
import bpy
from bpy.types import Object


def _add_curve(radius=1.0, order=5, resolution=64) -> Object:
    bpy.ops.curve.primitive_nurbs_path_add()
    ob = bpy.context.object
    ob.data.resolution_u = resolution

    spline = ob.data.splines[0]
    spline.order_u = order

    for p in spline.points:
        p.radius = radius

    return ob


def _add_mesh(location=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)) -> Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    ob = bpy.context.object
    ob.scale = scale
    return ob


def test_101() -> None:
    """Scaled object"""
    _add_mesh(scale=(1.5, 1.0, 1.0))


def test_102() -> None:
    """Empty object"""
    ob = _add_mesh()
    ob.data.clear_geometry()


def test_201() -> None:
    """Modifier order is incorrect"""
    ob = _add_mesh()
    ob.modifiers.new("Curve", "CURVE")
    ob.modifiers.new("Subd", "SUBSURF")


def test_202() -> None:
    """Cyclic dependency"""
    a = _add_mesh(location=(0.0, 0.0, 1.0), scale=(0.5, 0.5, 0.5))
    b = _add_mesh()
    a.modifiers.new("Project", "SHRINKWRAP").target = b
    b.modifiers.new("Bool", "BOOLEAN").object = a


def test_301() -> None:
    """Curve Radius deformation"""
    curve = _add_curve(radius=1.5)
    ob = _add_mesh()
    ob.modifiers.new("Curve", "CURVE").object = curve


def test_302() -> None:
    """Curve low Order"""
    _add_curve(order=3)


def test_303() -> None:
    """Curve low Resolution"""
    curve = _add_curve(resolution=12)
    ob = _add_mesh()
    ob.modifiers.new("Curve", "CURVE").object = curve


def test_401() -> None:
    """Collection uses default name"""
    coll = bpy.data.collections.new("Collection")
    bpy.context.scene.collection.children.link(coll)


def main() -> None:
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
