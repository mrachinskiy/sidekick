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


from bpy.types import PropertyGroup, AddonPreferences, Collection
from bpy.props import BoolProperty, EnumProperty, PointerProperty

from . import var, ui, mod_update


def upd_report(self, context):
    var.Report.cleanup()

    if self.show_problems:
        var.Report.get()


# Add-on preferences
# -----------------------------------


class Preferences(mod_update.Preferences, AddonPreferences):
    bl_idname = __package__

    # Interface
    # ---------------------------------

    overlay_style: EnumProperty(
        name="Overlay Style",
        items=(
            ("DETAILED", "Detailed", "Show full list of problems"),
            ("COMPACT", "Compact", "Show only number of problems"),
        ),
    )

    # Problems
    # ---------------------------------

    problem_ob_scale: BoolProperty(
        name="Non-uniform Scale",
        default=True,
    )
    problem_ob_empty: BoolProperty(
        name="Empty Object",
        default=True,
    )
    problem_curve_order: BoolProperty(
        name="Low Order",
        default=True,
    )
    problem_curve_resolution: BoolProperty(
        name="Low Resolution",
        default=True,
    )
    problem_curve_radius: BoolProperty(
        name="Radius Deformation",
        default=True,
    )
    problem_mod_order: BoolProperty(
        name="Wrong Order",
        default=True,
    )
    problem_cyclic_dep: BoolProperty(
        name="Cyclic Dependency",
        default=True,
    )
    problem_collection_name: BoolProperty(
        name="Collection Name",
        default=True,
    )
    problem_collection_visibility: BoolProperty(
        name="Collection Visibility",
        default=True,
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
