# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Sidekick scene linter for Blender.
#  Copyright (C) 2020  Mikhail Rachinskiy
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####


from typing import Iterator

import bpy
from bpy.types import Curve, Object, ObjectModifiers, LayerCollection
from mathutils import Vector

from . import problemlib


def _collection_walk(coll: LayerCollection) -> Iterator[LayerCollection]:
    for subcoll in coll.children:
        yield subcoll
        if subcoll.children:
            yield from _collection_walk(subcoll)


def _is_curve_bevel(curve: Curve) -> bool:
    return curve.bevel_depth or curve.extrude or curve.bevel_object is not None


def _is_gem_related(ob: Object) -> bool:
    return "gem" in ob or (ob.parent is not None and "gem" in ob.parent)


class Data:
    __slots__ = ("problems", "obs", "errors", "warns")

    def __init__(self) -> None:
        self.problems = []
        self.obs = []
        self.errors = 0
        self.warns = 0

    def cleanup(self) -> None:
        self.problems.clear()
        self.obs.clear()
        self.errors = 0
        self.warns = 0

    def get(self) -> None:
        self.cleanup()

        # Prepass
        # ----------------------------

        deformer_curves = set()

        for ob in bpy.context.scene.objects:
            for mod in ob.modifiers:
                if mod.type == "CURVE" and mod.object:
                    deformer_curves.add(mod.object)

        # Main pass
        # ----------------------------

        detected_problems = set()
        Check = Detect()

        for ob in bpy.context.scene.objects:

            ob_problems = set()

            if Check.ob_empty(ob):
                ob_problems.add(problemlib.ID_OB_EMPTY)

            else:

                if ob.type in {"CURVE", "FONT"}:

                    if _is_curve_bevel(ob.data) and Check.ob_scale(ob.scale):
                        ob_problems.add(problemlib.ID_OB_SCALE)

                    if ob in deformer_curves:
                        if Check.curve_radius(ob.data):
                            ob_problems.add(problemlib.ID_CURVE_RADIUS)
                        if Check.curve_resolution(ob.data):
                            ob_problems.add(problemlib.ID_CURVE_RESOLUTION)

                    if Check.curve_order(ob.data):
                        ob_problems.add(problemlib.ID_CURVE_ORDER)

                elif ob.type == "MESH":

                    if not _is_gem_related(ob) and Check.ob_scale(ob.scale):
                        ob_problems.add(problemlib.ID_OB_SCALE)

                    if ob.modifiers and Check.mod_order(ob.modifiers):
                        ob_problems.add(problemlib.ID_MOD_ORDER)

            if ob_problems:
                self.obs.append((ob.name, ob_problems))
                detected_problems |= ob_problems

        # Collection pass
        # ----------------------------

        for coll in _collection_walk(bpy.context.view_layer.layer_collection):
            if Check.collection_name(coll):
                detected_problems.add(problemlib.ID_COLLECTION_NAME)
            if Check.collection_visibility(coll):
                detected_problems.add(problemlib.ID_COLLECTION_VISIBILITY)

        # Report
        # ----------------------------

        for problem in problemlib.coll.values():
            if problem.code in detected_problems:
                self.problems.append(problem)

                if problem.type is problemlib.TYPE_ERROR:
                    self.errors += 1
                else:
                    self.warns += 1

        self.problems.sort(key=lambda x: x.type)


class Detect:
    __slots__ = (
        "ob_scale",
        "ob_empty",
        "curve_order",
        "curve_resolution",
        "curve_radius",
        "mod_order",
        "collection_name",
        "collection_visibility",
    )

    def __init__(self) -> None:
        prefs = bpy.context.preferences.addons[__package__].preferences

        for prop in self.__slots__:

            if getattr(prefs, f"problem_{prop}"):
                func = getattr(self, f"_{prop}")
            else:
                func = self.dummy

            setattr(self, prop, func)

        if len(bpy.data.collections) < 2:
            setattr(self, "collection_name", self.dummy)

    @staticmethod
    def dummy(x=None):
        return False

    @staticmethod
    def _ob_scale(scale: Vector) -> bool:
        return abs(scale.length_squared - 3.0) > 0.000001

    @staticmethod
    def _ob_empty(ob: Object) -> bool:
        methods = {
            "CURVE": lambda ob: not ob.data.splines,
            "MESH": lambda ob: not ob.data.vertices,
        }

        if (is_empty := methods.get(ob.type)) and is_empty(ob):
            if ob.modifiers:
                for mod in ob.modifiers:
                    if (
                        mod.type == "NODES" or
                        (mod.type == "BOOLEAN" and mod.operation == "UNION" and mod.object)
                    ):
                        return False
            return True

        return False

    @staticmethod
    def _curve_order(curve: Curve) -> bool:
        for spline in curve.splines:
            if spline.points and spline.order_u < 4:
                return True

        return False

    @staticmethod
    def _curve_resolution(curve: Curve) -> bool:
        return curve.splines[0].type != "POLY" and curve.resolution_u < 64

    @staticmethod
    def _curve_radius(curve: Curve) -> bool:
        if curve.use_radius and curve.splines:
            for p in (curve.splines[0].bezier_points or curve.splines[0].points):
                if p.radius != 1.0:
                    return True

        return False

    @staticmethod
    def _mod_order(modifiers: ObjectModifiers) -> bool:
        dmod = False
        dmods = {"CURVE", "LATTICE", "SHRINKWRAP", "SIMPLE_DEFORM"}

        for mod in modifiers:
            if mod.type in dmods:
                dmod = True
            elif mod.type == "SUBSURF" and dmod:
                return True

        return False

    @staticmethod
    def _collection_name(coll: LayerCollection) -> bool:
        return coll.name.startswith("Collection")

    @staticmethod
    def _collection_visibility(coll: LayerCollection) -> bool:
        if coll.hide_viewport:
            for ob in coll.collection.all_objects:
                if "gem" in ob:
                    return True
        return False
