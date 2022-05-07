# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2022 Mikhail Rachinskiy

from typing import Iterator, Any

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


class Scan:
    __slots__ = "problems", "problems_ignored", "obs", "obs_ignored", "errors", "warns"

    def __init__(self) -> None:
        self.problems = []
        self.problems_ignored = []
        self.obs = []
        self.obs_ignored = []
        self.errors = 0
        self.warns = 0

    def cleanup(self) -> None:
        self.problems.clear()
        self.problems_ignored.clear()
        self.obs.clear()
        self.obs_ignored.clear()
        self.errors = 0
        self.warns = 0

    def get(self) -> None:
        self.cleanup()
        scene = bpy.context.scene
        detected_problems = set()
        ignored_problems = set()
        Check = _Detect()

        # Collection pass
        # ----------------------------

        for coll in _collection_walk(bpy.context.view_layer.layer_collection):
            Check.do(problemlib.ID_COLLECTION_NAME, coll)
            Check.do(problemlib.ID_COLLECTION_VISIBILITY, coll)

        detected_problems |= Check.found

        # Object prepass
        # ----------------------------

        deformer_curves = set()

        for ob in scene.objects:
            for mod in ob.modifiers:
                if mod.type == "CURVE" and mod.object:
                    deformer_curves.add(mod.object)

        # Object pass
        # ----------------------------

        for ob in scene.objects:
            Check.found = set()
            Check.ignored = set(ob["sidekick_ignore"]) if "sidekick_ignore" in ob else set()

            if not Check.do(problemlib.ID_OB_EMPTY, ob):

                if ob.type in {"CURVE", "FONT"}:
                    if _is_curve_bevel(ob.data):
                        Check.do(problemlib.ID_OB_SCALE, ob.scale)
                    if ob in deformer_curves:
                        Check.do(problemlib.ID_CURVE_RADIUS, ob.data)
                        Check.do(problemlib.ID_CURVE_RESOLUTION, ob.data)
                    Check.do(problemlib.ID_CURVE_ORDER, ob.data)

                elif ob.type == "MESH":
                    if not _is_gem_related(ob):
                        Check.do(problemlib.ID_OB_SCALE, ob.scale)
                    if ob.modifiers:
                        Check.do(problemlib.ID_MOD_ORDER, ob.modifiers)
                        Check.do(problemlib.ID_CYCLIC_DEP, ob)

            if Check.found:
                self.obs.append((ob.name, Check.found))
                detected_problems |= Check.found

            if Check.ignored:
                self.obs_ignored.append((ob.name, Check.ignored))
                ignored_problems |= Check.ignored

        # Report
        # ----------------------------

        for problem in problemlib.coll.values():

            if problem.code in detected_problems:
                self.problems.append(problem)
                if problem.type is problemlib.TYPE_ERROR:
                    self.errors += 1
                else:
                    self.warns += 1

            if problem.code in ignored_problems:
                self.problems_ignored.append(problem)

        self.problems.sort(key=lambda x: x.type)
        self.problems_ignored.sort(key=lambda x: x.type)


class _Detect:
    __slots__ = "found", "_ignored", "_disabled", "_excluded"
    found: set
    _ignored: set
    _disabled: set
    _excluded: set

    def __init__(self) -> None:
        prefs = bpy.context.preferences.addons[__package__].preferences
        self.found = set()
        self._disabled = {code for code in problemlib.coll.keys() if not getattr(prefs, f"problem_{code}")}

        if len(bpy.data.collections) < 2:
            self._disabled.add(problemlib.ID_COLLECTION_NAME)

        self._excluded = self._disabled

    @property
    def ignored(self) -> set:
        return self._ignored

    @ignored.setter
    def ignored(self, value: set) -> None:
        self._ignored = value
        self._excluded = self._disabled | value

    def do(self, code: int, value: Any) -> bool:
        if code not in self._excluded and getattr(self, f"_{code}")(value):
            self.found.add(code)
            return True
        return False

    @staticmethod
    def _101(scale: Vector) -> bool:
        return abs(scale.length_squared - 3.0) > 1e-6

    @staticmethod
    def _102(ob: Object) -> bool:
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
    def _201(modifiers: ObjectModifiers) -> bool:
        dmod = False
        dmods = {"CURVE", "LATTICE", "SHRINKWRAP", "SIMPLE_DEFORM"}

        for mod in modifiers:
            if mod.type in dmods:
                dmod = True
            elif mod.type == "SUBSURF" and dmod:
                return True

        return False

    @staticmethod
    def _202(ob: Object) -> bool:
        for mod in ob.modifiers:
            if mod.type == "SHRINKWRAP" and mod.target:
                for tmod in mod.target.modifiers:
                    if tmod.type == "BOOLEAN":
                        return (
                            tmod.object == ob or
                            ob in {
                                mod.object for mod in tmod.object.modifiers
                                if mod.type == "BOOLEAN"
                            }
                        )
                break

        return False

    @staticmethod
    def _301(curve: Curve) -> bool:
        if curve.use_radius and curve.splines:
            for p in (curve.splines[0].bezier_points or curve.splines[0].points):
                if p.radius != 1.0:
                    return True

        return False

    @staticmethod
    def _302(curve: Curve) -> bool:
        for spline in curve.splines:
            if spline.points and spline.order_u < 4:
                return True

        return False

    @staticmethod
    def _303(curve: Curve) -> bool:
        return curve.splines[0].type != "POLY" and curve.resolution_u < 64

    @staticmethod
    def _401(coll: LayerCollection) -> bool:
        return coll.name.startswith("Collection")

    @staticmethod
    def _402(coll: LayerCollection) -> bool:
        if coll.hide_viewport:
            for ob in coll.collection.all_objects:
                if "gem" in ob:
                    return True
        return False
