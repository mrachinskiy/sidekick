# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2022 Mikhail Rachinskiy

from bpy.types import PropertyGroup, AddonPreferences, Collection
from bpy.props import BoolProperty, EnumProperty, PointerProperty

from . import var, ui, mod_update, problemlib


def upd_report(self, context):
    var.Report.cleanup()

    if self.show_problems:
        var.Report.get()


# Add-on preferences
# -----------------------------------


def _cls_Problems():
    x = "class Problems:"
    for code, problem in problemlib.coll.items():
        x += f'\n problem_{code}: BoolProperty(name="{problem.title}", description="{code}", default=True)'
    return x


exec(_cls_Problems())


class Preferences(Problems, mod_update.Preferences, AddonPreferences):
    bl_idname = __package__

    overlay_style: EnumProperty(
        name="Overlay Style",
        items=(
            ("DETAILED", "Detailed", "Show full list of problems"),
            ("COMPACT", "Compact", "Show only number of problems"),
        ),
    )

    def draw(self, context):
        ui.prefs_ui(self, context)


# Window manager properties
# -----------------------------------


class WmProperties(PropertyGroup):
    prefs_active_tab: EnumProperty(
        items=(
            ("INTERFACE", "Interface", ""),
            ("PROBLEMS", "Problems", ""),
            ("UPDATES", "Updates", ""),
        ),
    )
    show_problems: BoolProperty(
        name="Problems",
        description="Show scene problems",
        default=True,
        update=upd_report,
    )


# Scene properties
# ------------------------------------------


class SceneProperties(PropertyGroup):
    exceptions: PointerProperty(
        type=Collection,
        name="Exceptions",
        description="Collection of objects excluded from scene inspection",
    )
