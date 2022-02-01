# ##### BEGIN GPL LICENSE BLOCK #####
#
#  Sidekick scene linter for Blender.
#  Copyright (C) 2020-2022  Mikhail Rachinskiy
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


import bpy
from bpy.types import Operator
from bpy.props import IntProperty
from bpy.app.translations import pgettext_tip as _

from . import var, problemlib


class OBJECT_OT_select(Operator):
    bl_label = "Select"
    bl_description = "Select visible objects with detected problem"
    bl_idname = "object.sidekick_select"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    code: IntProperty(options={"SKIP_SAVE", "HIDDEN"})

    def execute(self, context):
        ob_get = bpy.data.objects.get
        obs = set(ob_get(ob_name) for ob_name, problems in var.Report.obs if self.code in problems)
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


class SCENE_OT_test(Operator):
    bl_label = "Add Problems"
    bl_description = "Create test case for problem detection"
    bl_idname = "wm.sidekick_test"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        coll = bpy.data.collections.new("Collection All Problems")
        context.scene.collection.children.link(coll)
        lcoll = context.view_layer.layer_collection.children[-1]
        context.view_layer.active_layer_collection = lcoll

        subcoll = bpy.data.collections.new("Hidden Problem")
        coll.children.link(subcoll)
        lcoll.children[0].hide_viewport = True

        bpy.ops.mesh.primitive_cone_add()
        ob_gem = context.object
        ob_gem.name = "Gem"
        ob_gem["gem"] = {
            "cut": "NONE",
            "stone": "NONE",
        }
        coll.objects.unlink(ob_gem)
        subcoll.objects.link(ob_gem)

        bpy.ops.curve.primitive_nurbs_path_add()
        ob_curve = context.object
        spline = ob_curve.data.splines[0]
        spline.order_u = 3
        for p in spline.points:
            p.radius = 1.5

        bpy.ops.mesh.primitive_cube_add()
        ob_mesh = context.object
        ob_mesh.scale.x = 1.5
        ob_mesh.modifiers.new("Curve", "CURVE").object = ob_curve
        ob_mesh.modifiers.new("Subd", "SUBSURF")

        bpy.ops.mesh.primitive_plane_add()
        ob_mesh_empty = context.object
        ob_mesh_empty.name = "Empty Mesh"
        ob_mesh_empty.data.clear_geometry()

        # Cyclic dependency
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 1.5))
        ob_a = context.object
        ob_a.name = "Cyclic Dependency Project"

        bpy.ops.mesh.primitive_cube_add()
        ob_b = context.object
        ob_b.name = "Cyclic Dependency Boolean"

        ob_a.modifiers.new("Project", "SHRINKWRAP").target = ob_b
        ob_a.modifiers.new("Thick", "SOLIDIFY").offset = 0.0

        ob_b.modifiers.new("Bool", "BOOLEAN").object = ob_a

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_confirm(self, event)
