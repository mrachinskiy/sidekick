# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2023 Mikhail Rachinskiy

import bpy
from bpy.types import Operator, Collection, Object
from bpy.props import IntProperty, BoolProperty
from bpy.app.translations import pgettext_tip as _

from . import var, problemlib


class OBJECT_OT_select(Operator):
    bl_label = "Select"
    bl_description = "Select visible objects with detected problem"
    bl_idname = "object.sidekick_select"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    code: IntProperty(options={"SKIP_SAVE", "HIDDEN"})
    use_ignored: BoolProperty(options={"SKIP_SAVE", "HIDDEN"})

    def execute(self, context):
        ob_get = bpy.data.objects.get
        report_obs = var.Report.obs_ignored if self.use_ignored else var.Report.obs
        obs = set(ob_get(ob_name) for ob_name, problems in report_obs if self.code in problems)
        selection_failed = False

        for ob in context.scene.objects:
            is_problem = ob in obs
            ob.select_set(is_problem)

            if is_problem and not (ob.visible_get() and ob.select_get()):
                selection_failed = True

        if context.selected_objects and not context.view_layer.objects.active.select_get():
            context.view_layer.objects.active = context.selected_objects[0]

        if selection_failed:
            self.report({"ERROR"}, "Can't select hidden or unselectable objects")

        return {"FINISHED"}


class WM_OT_show_description(Operator):
    bl_label = "Show Description"
    bl_description = "Show problem description"
    bl_idname = "wm.sidekick_show_description"
    bl_translation_context = "*"
    bl_options = {"INTERNAL"}

    code: IntProperty(options={"SKIP_SAVE", "HIDDEN"})

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        import textwrap

        layout = self.layout
        problem = problemlib.coll[self.code]

        box = layout.box()
        box.label(text=problem.title, icon="CANCEL" if problem.type is problemlib.TYPE_ERROR else "ERROR")

        for paragraph in _(problem.desc).split("\n\n"):
            col = box.column(align=True)
            for chunk in paragraph.split("\n"):
                for line in textwrap.wrap(chunk, 45):
                    col.label(text=line)

    def invoke(self, context, event):
        if bpy.app.translations.locale == "ru_RU":
            width = 320
        else:
            width = 300

        wm = context.window_manager
        return wm.invoke_popup(self, width=width)


def _cls_Problems():
    x = "class Problems:"
    for code, problem in problemlib.coll.items():
        if not problem.select:
            continue
        x += f'\n problem_{code}: BoolProperty(name="{problem.title}", description="{code}", options={{"SKIP_SAVE", "HIDDEN"}})'
    return x


exec(_cls_Problems())


class OBJECT_OT_ignore(Problems, Operator):
    bl_label = "Sidekick Ignore"
    bl_description = "Specify problems to ignore for selected objects"
    bl_idname = "object.sidekick_ignore"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        codes = [
            code for code, problem in problemlib.coll.items()
            if problem.select and getattr(self, f"problem_{code}")
        ]

        if codes:
            for ob in context.selected_objects:
                ob["sidekick_ignore"] = codes
        else:
            for ob in context.selected_objects:
                if "sidekick_ignore" in ob:
                    del ob["sidekick_ignore"]

        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        for code, problem in problemlib.coll.items():
            if not problem.select:
                continue

            if code == 101:
                col = layout.column(heading="Object")
            elif code == 201:
                col = layout.column(heading="Relations")
            elif code == 301:
                col = layout.column(heading="Object Data")

            col.prop(self, f"problem_{code}")

        layout.separator()

    def invoke(self, context, event):
        if not context.selected_objects:
            return {"CANCELLED"}

        if context.object is not None and (codes := context.object.get("sidekick_ignore")):
            for code in codes:
                if hasattr(self, f"problem_{code}"):
                    setattr(self, f"problem_{code}", True)

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SCENE_OT_test(Operator):
    bl_label = "Add Problems"
    bl_description = "Create test case for problem detection"
    bl_idname = "wm.sidekick_test"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        coll = bpy.data.collections.new("Sidekick")
        context.scene.collection.children.link(coll)
        view_layer = context.view_layer
        view_layer.active_layer_collection = view_layer.layer_collection.children[-1]

        for code in problemlib.coll.keys():
            getattr(self, f"_test_{code}")()

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)

    @staticmethod
    def _add_move_to_collection(name: str, obs: list[Object]) -> Collection:
        coll = bpy.data.collections.new(name)
        bpy.context.collection.children.link(coll)
        for ob in obs:
            bpy.context.collection.objects.unlink(ob)
            coll.objects.link(ob)
        return coll

    @staticmethod
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

    @staticmethod
    def _add_mesh(name: str, location=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)) -> Object:
        bpy.ops.mesh.primitive_cube_add(location=location)
        ob = bpy.context.object
        ob.name = name
        ob.scale=scale
        return ob

    def _test_101(self) -> None:
        self._add_mesh("Object Scale", scale=(1.5, 1.0, 1.0))

    def _test_102(self) -> None:
        ob = self._add_mesh("Empty Mesh")
        ob.data.clear_geometry()

    def _test_201(self) -> None:
        ob = self._add_mesh("Wrong Mod Order")
        ob.modifiers.new("Curve", "CURVE")
        ob.modifiers.new("Subd", "SUBSURF")

    def _test_202(self) -> None:
        a = self._add_mesh("AB", location=(0.0, 0.0, 1.0), scale=(0.5, 0.5, 0.5))
        b = self._add_mesh("BA")
        a.modifiers.new("Project", "SHRINKWRAP").target = b
        b.modifiers.new("Bool", "BOOLEAN").object = a
        self._add_move_to_collection("Cyclic Dependency", (a, b))

    def _test_301(self) -> None:
        curve = self._add_curve("Radius", radius=1.5)
        mesh = self._add_mesh("Radius Deform")
        mesh.modifiers.new("Curve", "CURVE").object = curve
        self._add_move_to_collection("Curve Radius", (curve, mesh))

    def _test_302(self) -> None:
        self._add_curve("Low Order", order=3)

    def _test_303(self) -> None:
        curve = self._add_curve("Low Resolution", resolution=12)
        mesh = self._add_mesh("Resolution Deform")
        mesh.modifiers.new("Curve", "CURVE").object = curve
        self._add_move_to_collection("Curve Resolution", (curve, mesh))

    @staticmethod
    def _test_401() -> None:
        bpy.context.collection.name = "Collection All Problems"

    def _test_402(self) -> None:
        ob = self._add_mesh("Fake Gem")
        ob["gem"] = {"cut": "NONE", "stone": "NONE"}
        self._add_move_to_collection("Visibility", (ob,))
        bpy.context.view_layer.active_layer_collection.children[-1].hide_viewport = True
