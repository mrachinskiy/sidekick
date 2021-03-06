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


bl_info = {
    "name": "Sidekick",
    "author": "Mikhail Rachinskiy",
    "version": (1, 0, 0),
    "blender": (2, 93, 0),
    "location": "3D View > Header > Problems",
    "description": "Detect common modeling mistakes in the scene.",
    "doc_url": "https://github.com/mrachinskiy/sidekick#readme",
    "tracker_url": "https://github.com/mrachinskiy/sidekick/issues",
    "category": "3D View",
}


if "bpy" in locals():
    _essential.reload_recursive(var.ADDON_DIR, locals())
else:
    import bpy
    from bpy.props import PointerProperty

    from . import _essential, var

    _essential.check(var.ADDON_DIR / "mod_update", bl_info["blender"])

    from . import (
        localization,
        mod_update,
        onscreen,
        operators,
        preferences,
        ui,
    )


classes = (
    preferences.Preferences,
    preferences.WmProperties,
    ui.VIEW3D_PT_sidekick_problems,
    operators.OBJECT_OT_select,
    operators.WM_OT_show_description,
    operators.SCENE_OT_test,
    *mod_update.ops,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.sidekick = PointerProperty(type=preferences.WmProperties)

    # Overlays option
    # ---------------------------

    bpy.types.VIEW3D_HT_header.append(ui.draw_3dview_header)

    # Handlers
    # ---------------------------

    onscreen.handler_add()

    # mod_update
    # ---------------------------

    mod_update.init(
        addon_version=bl_info["version"],
        repo_url="mrachinskiy/sidekick",
    )

    # Translations
    # ---------------------------

    bpy.app.translations.register(__name__, localization.DICTIONARY)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.sidekick

    # Overlays option
    # ---------------------------

    bpy.types.VIEW3D_HT_header.remove(ui.draw_3dview_header)

    # Handlers
    # ---------------------------

    onscreen.handler_del()

    # Translations
    # ---------------------------

    bpy.app.translations.unregister(__name__)


if __name__ == "__main__":
    register()
