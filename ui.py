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


import bpy
from bpy.types import Panel

from . import var, mod_update, problemlib


def upd_problems_popover_width():
    if bpy.app.translations.locale == "ru_RU":
        width = 15
    else:
        width = 12

    if VIEW3D_PT_sidekick_problems.bl_ui_units_x == width:
        return

    VIEW3D_PT_sidekick_problems.bl_ui_units_x = width
    bpy.utils.unregister_class(VIEW3D_PT_sidekick_problems)
    bpy.utils.register_class(VIEW3D_PT_sidekick_problems)


def draw_3dview_header(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.prop(context.window_manager.sidekick, "show_problems", text="", icon="ERROR")
    row.popover(panel="VIEW3D_PT_sidekick_problems", text="")


class VIEW3D_PT_sidekick_problems(Panel):
    bl_label = "Problems"
    bl_space_type = "VIEW_3D"
    bl_region_type = "HEADER"
    bl_context = "objectmode"
    bl_ui_units_x = 12
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        if mod_update.state.update_available:
            layout.label(text="Update")
            mod_update.sidebar_ui(layout)

        layout.label(text="Problems")

        if not var.Report.problems:
            box = layout.box()
            box.label(text="No problems found")
            return

        col = layout.column()

        for problem in var.Report.problems:
            row = col.row()

            row1 = row.row()
            row1.alignment = "LEFT"
            row1.operator(
                "wm.sidekick_show_description",
                text=problem.title,
                icon="CANCEL" if problem.type is problemlib.TYPE_ERROR else "ERROR",
                emboss=False,
            ).code = problem.code

            if problem.selection:
                row2 = row.row()
                row2.alignment = "RIGHT"
                row2.operator("object.sidekick_select", text="", icon="RESTRICT_SELECT_OFF", emboss=False).code = problem.code


# Preferences
# ---------------------------


def prefs_ui(self, context):
    wm_props = context.window_manager.sidekick
    active_tab = wm_props.prefs_active_tab

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    split = layout.split(factor=0.25)
    col = split.column()
    col.use_property_split = False
    col.scale_y = 1.3
    col.prop(wm_props, "prefs_active_tab", expand=True)

    box = split.box()

    if active_tab == "INTERFACE":
        box.prop(self, "overlay_style")

    if active_tab == "PROBLEMS":
        col = box.column(heading="Object")
        col.prop(self, "problem_ob_scale")
        col.prop(self, "problem_ob_empty")

        col = box.column(heading="Curve")
        col.prop(self, "problem_curve_order")
        col.prop(self, "problem_curve_resolution")
        col.prop(self, "problem_curve_radius")

        col = box.column(heading="Modifiers")
        col.prop(self, "problem_mod_order")

        col = box.column(heading="Scene")
        col.prop(self, "problem_collection_name")

    elif active_tab == "UPDATES":
        mod_update.prefs_ui(self, box)
