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
    "blender": (2, 90, 0),
    "location": "3D View > Header > Problems",
    "description": "Detect common mistakes and give recommendations.",
    "doc_url": "https://github.com/mrachinskiy/sidekick#readme",
    "tracker_url": "https://github.com/mrachinskiy/sidekick/issues",
    "category": "3D View",
}


if "bpy" in locals():
    import os
    from typing import Dict
    from types import ModuleType


    def reload_recursive(path: str, mods: Dict[str, ModuleType]) -> None:
        import importlib

        for entry in os.scandir(path):

            if entry.is_file() and entry.name.endswith(".py") and not entry.name.startswith("__"):
                filename, _ = os.path.splitext(entry.name)

                if filename in mods:
                    importlib.reload(mods[filename])

            elif entry.is_dir() and not entry.name.startswith((".", "__")):

                if entry.name in mods:
                    importlib.reload(mods[entry.name])
                    reload_recursive(entry.path, mods[entry.name].__dict__)
                    continue

                reload_recursive(entry.path, mods)


    reload_recursive(os.path.dirname(__file__), locals())
else:
    import bpy
    from bpy.props import PointerProperty

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
    if bl_info["blender"] > bpy.app.version:
        addon_name = bl_info["name"].upper()
        addon_ver = ".".join(str(x) for x in bl_info["version"])
        blender_ver = ".".join(str(x) for x in bl_info["blender"][:2])
        requirements_check = RuntimeError(
            f"\n!!! BLENDER {blender_ver} IS REQUIRED FOR {addon_name} {addon_ver} !!!"
            "\n!!! READ INSTALLATION GUIDE !!!"
        )
        raise requirements_check

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
        translation_dict=localization.DICTIONARY,
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
