# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2022 Mikhail Rachinskiy

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
    row = self.layout.row(align=True)
    row.prop(context.window_manager.sidekick, "show_problems", text="", icon="ERROR")
    row.popover(panel="VIEW3D_PT_sidekick_problems", text="")


def draw_object_context_menu(self, context):
    layout = self.layout
    layout.operator_context = "INVOKE_DEFAULT"
    layout.separator()
    layout.operator("object.sidekick_ignore")


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

        if var.Report.problems:
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

                if problem.select:
                    row2 = row.row()
                    row2.alignment = "RIGHT"
                    row2.operator("object.sidekick_select", text="", icon="RESTRICT_SELECT_OFF", emboss=False).code = problem.code
        else:
            box = layout.box()
            box.label(text="No problems found")

        if var.Report.problems_ignored:
            layout.separator()

            layout.label(text="Ignored")

            col = layout.column()
            col.active = False

            for problem in var.Report.problems_ignored:
                row = col.row()

                row1 = row.row()
                row1.alignment = "LEFT"
                row1.operator(
                    "wm.sidekick_show_description",
                    text=problem.title,
                    icon="CANCEL" if problem.type is problemlib.TYPE_ERROR else "ERROR",
                    emboss=False,
                ).code = problem.code

                if problem.select:
                    row2 = row.row()
                    row2.alignment = "RIGHT"
                    op = row2.operator("object.sidekick_select", text="", icon="RESTRICT_SELECT_OFF", emboss=False)
                    op.code = problem.code
                    op.use_ignored = True


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
        for code in problemlib.coll.keys():
            if code == 101:
                col = box.column(heading="Object")
            elif code == 201:
                col = box.column(heading="Relations")
            elif code == 301:
                col = box.column(heading="Object Data")
            elif code == 401:
                col = box.column(heading="Scene")

            col.prop(self, f"problem_{code}")

    elif active_tab == "UPDATES":
        mod_update.prefs_ui(self, box)
