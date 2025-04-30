# SPDX-FileCopyrightText: 2020-2024 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Panel, PropertyGroup, UILayout

from . import problemlib, var


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


def _prop_panel(layout: UILayout, data: PropertyGroup, prop: str) -> bool:
    enabled = getattr(data, prop)

    sub = layout.row()
    sub.use_property_split = False
    sub.alignment = "LEFT"
    sub.prop(data, prop, icon="DOWNARROW_HLT" if enabled else "RIGHTARROW", emboss=False)

    return enabled


def prefs_ui(self, context):
    wm_props = context.window_manager.sidekick

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False

    main = layout.column()

    if _prop_panel(main, wm_props, "prefs_show_interface"):
        main.prop(self, "overlay_style")

    if _prop_panel(main, wm_props, "prefs_show_problems"):
        for code in problemlib.coll.keys():
            if code == 101:
                col = main.column(heading="Object")
            elif code == 201:
                col = main.column(heading="Relations")
            elif code == 301:
                col = main.column(heading="Object Data")
            elif code == 401:
                col = main.column(heading="Scene")

            col.prop(self, f"problem_{code}")
