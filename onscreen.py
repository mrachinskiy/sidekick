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


from typing import Tuple, Iterable, Iterator, Optional
from math import tau, sin, cos

import bpy
from bpy.app.translations import pgettext_iface as _t
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from . import var, ui, problemlib, mod_update


_handler = None


def _refresh() -> float:
    is_refreshed = False

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D" and area.spaces.active.overlay.show_overlays:
                if not is_refreshed:
                    var.Report.get()
                    is_refreshed = True
                area.tag_redraw()

    ui.upd_problems_popover_width()

    return 5.0


def handler_add():
    global _handler

    if _handler is None:
        bpy.app.timers.register(_refresh, persistent=True)
        _handler = bpy.types.SpaceView3D.draw_handler_add(_draw, (), "WINDOW", "POST_PIXEL")


def handler_del():
    global _handler

    if _handler is not None:
        bpy.app.timers.unregister(_refresh)
        bpy.types.SpaceView3D.draw_handler_remove(_handler, "WINDOW")
        var.Report.cleanup()
        _handler = None


def handler_toggle(self, context):
    if context.area.type == "VIEW_3D":
        if self.show_problems:
            handler_add()
        else:
            handler_del()


def _draw():
    context = bpy.context
    overlay = context.space_data.overlay

    if not overlay.show_overlays:
        return

    prefs = context.preferences
    ui_scale = prefs.view.ui_scale
    style_detailed = prefs.addons[__package__].preferences.overlay_style == "DETAILED"

    fontid = 2
    fontsize = round(prefs.ui_styles[0].widget_label.points * ui_scale)

    # Position

    x = 20
    y = 5

    for region in context.area.regions:
        if region.type == "HEADER":
            y += region.height
        elif region.type == "TOOLS":
            x += region.width

    if overlay.show_text:
        view = prefs.view
        if view.show_object_info:
            y += 25
        if view.show_view_name:
            y += 25
        elif view.show_playback_fps and context.screen.is_animation_playing:
            y += 25

    if overlay.show_stats:
        y += 130

    y = context.region.height - round(y * ui_scale)

    # Color

    color_text = prefs.themes[0].view_3d.space.text_hi
    color_blue = (0.0, 0.6, 1.0, 1.0)
    color_red = (1.0, 0.25, 0.25, 1.0)
    color_orange = (1.0, 0.8, 0.2, 1.0)
    shader = gpu.shader.from_builtin("2D_UNIFORM_COLOR")

    # Line height

    blf.size(fontid, fontsize, 104)
    _, font_h = blf.dimensions(fontid, "Font Height")
    font_row_height = round(font_h * 1.7)
    icon_size = font_h / 2

    if style_detailed:

        for problem_type, problem_title in _fmt_detailed(var.Report.problems):

            if problem_type is problemlib.TYPE_ERROR:
                color = color_red
                icon = _circle
            elif problem_type is problemlib.TYPE_WARN:
                color = color_orange
                icon = _triangle
            else:
                color = color_blue
                icon = _circle

            y -= font_row_height

            shader.bind()
            shader.uniform_float("color", color)
            batch_font = batch_for_shader(shader, "TRI_FAN", {"pos": icon(icon_size, x, y)})
            batch_font.draw(shader)
            x_ofst = x + font_h

            blf.position(fontid, x_ofst, y, 0.0)
            blf.color(fontid, *color_text, 1.0)
            blf.draw(fontid, problem_title)

    else:

        y -= font_row_height

        for num, color, icon in (
            (str(int(mod_update.state.update_available)), color_blue, _circle),
            (str(var.Report.errors), color_red, _circle),
            (str(var.Report.warns), color_orange, _triangle),
        ):
            if num == "0":
                continue

            shader.bind()
            shader.uniform_float("color", color)
            batch_font = batch_for_shader(shader, "TRI_FAN", {"pos": icon(icon_size, x, y)})
            batch_font.draw(shader)
            x += font_h

            blf.position(fontid, x, y, 0.0)
            blf.color(fontid, *color_text, 1.0)
            blf.draw(fontid, num)

            # Item spacing
            font_w, _ = blf.dimensions(fontid, num)
            x += font_w + font_h


def _circle(radius: float, x: int, y: int) -> Tuple[Tuple[float, float], ...]:
    y += radius / 1.3
    angle = tau / 12

    return tuple(
        (
            sin(i * angle) * radius + x,
            cos(i * angle) * radius + y,
        )
        for i in range(12)
    )


def _triangle(radius: float, x: int, y: int) -> Tuple[Tuple[float, float], ...]:
    y -= radius / 4

    return (
        (x, y + radius * 2),
        (x - radius, y),
        (x + radius, y),
    )


def _fmt_detailed(seq: Iterable) -> Iterator[Tuple[Optional[int], str]]:
    if mod_update.state.update_available:
        yield None, _t("Update {} is available").format(mod_update.state.update_version)

    for x in seq:
        yield x.type, _t(x.title)
