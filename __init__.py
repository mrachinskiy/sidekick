# SPDX-FileCopyrightText: 2020-2024 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later


if "bpy" in locals():
    from . import var
    essentials.reload_recursive(var.ADDON_DIR, locals())
else:
    import bpy
    from bpy.props import PointerProperty

    from . import essentials, localization, onscreen, operators, preferences, ui


classes = essentials.get_classes((preferences, operators, ui))


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
