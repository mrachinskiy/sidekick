# SPDX-FileCopyrightText: 2020-2024 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later


if "bpy" in locals():
    _essential.reload_recursive(var.ADDON_DIR, locals())
else:
    from . import _essential, var

    _essential.check(var.ADDON_DIR / "mod_update", var.MANIFEST["blender_version_min"])

    import bpy
    from bpy.props import PointerProperty

    from . import localization, mod_update, onscreen, operators, preferences, ui


classes = (
    preferences.Preferences,
    preferences.WmProperties,
    preferences.SceneProperties,
    ui.VIEW3D_PT_sidekick_problems,
    operators.OBJECT_OT_select,
    operators.WM_OT_show_description,
    operators.OBJECT_OT_ignore,
    operators.SCENE_OT_test,
    *mod_update.ops,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.sidekick = PointerProperty(type=preferences.WmProperties)
    bpy.types.Scene.sidekick = PointerProperty(type=preferences.SceneProperties)

    # Menu
    # ---------------------------

    bpy.types.VIEW3D_MT_object_context_menu.append(ui.draw_object_context_menu)

    # Overlays option
    # ---------------------------

    bpy.types.VIEW3D_HT_header.append(ui.draw_3dview_header)

    # Handlers
    # ---------------------------

    onscreen.handler_add()

    # mod_update
    # ---------------------------

    mod_update.init(repo_url="mrachinskiy/sidekick")

    # Translations
    # ---------------------------

    bpy.app.translations.register(__name__, localization.DICTIONARY)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.sidekick
    del bpy.types.Scene.sidekick

    # Menu
    # ---------------------------

    bpy.types.VIEW3D_MT_object_context_menu.remove(ui.draw_object_context_menu)

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
