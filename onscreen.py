# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2023 Mikhail Rachinskiy

import itertools
from collections.abc import Iterable, Iterator
from functools import lru_cache
from math import cos, sin, tau

import blf
import bpy
import gpu
from bpy.app.translations import pgettext_iface as _t
from gpu.types import GPUShader
from gpu_extras.batch import batch_for_shader

from . import mod_update, problemlib, ui, var


_handler = None


def _refresh() -> float:
    if bpy.context.window_manager.sidekick.show_problems:

        var.Report.get()

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D" and area.spaces.active.overlay.show_overlays:
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


def _draw_icon(shader: GPUShader, color: tuple[float], icon_co: tuple[tuple[float]]) -> None:
    gpu.state.blend_set("ALPHA")
    shader.uniform_float("color", color)
    batch = batch_for_shader(shader, "LINES", {"pos": icon_co})
    batch.draw(shader)


def _draw_text(fontid: int, font_h: float, color: tuple[float], text: str):
    blf.position(fontid, font_h, 0.0, 0.0)
    blf.color(fontid, *color, 1.0)
    blf.draw(fontid, text)


def _draw():
    context = bpy.context
    overlay = context.space_data.overlay

    if not var.Report.problems or not context.window_manager.sidekick.show_problems or not overlay.show_overlays:
        return

    prefs = context.preferences
    ui_scale = prefs.view.ui_scale
    style_detailed = prefs.addons[__package__].preferences.overlay_style == "DETAILED"
    fontscale = prefs.ui_styles[0].widget_label.points * ui_scale / 11  # 11 is the default font size

    fontid = 0
    fontsize = round(fontscale * 17)
    blf.size(fontid, fontsize)
    _, font_h = blf.dimensions(fontid, "Font Height")
    row_height = round(font_h * 1.7)
    icon_size = round(font_h / 2)

    shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
    shader.uniform_float("viewportSize", (context.area.width, context.area.height))
    shader.uniform_float("lineWidth", 1.8)

    # Color

    color_text = prefs.themes[0].view_3d.space.text_hi
    color_update = (0.0, 0.6, 1.0, 1.0)
    color_error = (1.0, 0.25, 0.25, 1.0)
    color_warn = (1.0, 0.8, 0.2, 1.0)

    # Starting position

    x = round(12 * ui_scale) + icon_size
    y = round(5 * ui_scale)

    for region in context.area.regions:
        if region.type in {"HEADER", "TOOL_HEADER"}:
            y += region.height
        elif region.type == "TOOLS":
            x += region.width

    # Viewport text offset
    # -------------------------------------

    _y = 0

    if overlay.show_text:
        view = prefs.view
        if view.show_object_info:
            _y += 25
        if view.show_view_name or (view.show_playback_fps and context.screen.is_animation_playing):
            _y += 25

    if overlay.show_stats:
        _y += 130

    y += round(_y * fontscale)

    # -------------------------------------

    y = context.region.height - y
    gpu.matrix.translate((x, y))

    if style_detailed:

        for problem_type, problem_title in _fmt_detailed(var.Report.problems):

            if problem_type is problemlib.TYPE_ERROR:
                color = color_error
                icon = _icon_error
            elif problem_type is problemlib.TYPE_WARN:
                color = color_warn
                icon = _icon_warning
            else:
                color = color_update
                icon = _icon_update

            gpu.matrix.translate((0.0, -row_height))

            _draw_icon(shader, color, icon(icon_size))
            _draw_text(fontid, font_h, color_text, problem_title)

    else:

        gpu.matrix.translate((0.0, -row_height))

        for num, color, icon in (
            (str(int(mod_update.state.update_available)), color_update, _icon_update),
            (str(var.Report.errors), color_error, _icon_error),
            (str(var.Report.warns), color_warn, _icon_warning),
        ):
            if num == "0":
                continue

            _draw_icon(shader, color, icon(icon_size))
            _draw_text(fontid, font_h, color_text, num)

            font_w, _ = blf.dimensions(fontid, num)
            gpu.matrix.translate((font_h * 2 + font_w, 0.0))

    gpu.state.blend_set("NONE")
    gpu.matrix.load_identity()


# Icons
# -------------------------------------


@lru_cache(maxsize=1)
def _icon_update(radius: float) -> tuple[tuple[float, float], ...]:
    radius *= 1.05
    y = radius / 1.3
    angle = tau / 12

    circle = [
        (
            sin(i * angle) * radius,
            cos(i * angle) * radius + y,
        )
        for i in range(10)
    ]

    radius *= 0.4
    x, y = circle[-1]
    x += radius * 0.1

    arrow = (
        (x - radius, y),
        (x, y + radius * 1.7),
        (x + radius, y),
    )

    return (*_co_pairs(circle), *_co_pairs(arrow))


@lru_cache(maxsize=1)
def _icon_error(radius: float) -> tuple[tuple[float, float], ...]:
    radius *= 1.15
    y = radius / 1.3
    angle = tau / 12

    circle = [
        (
            sin(i * angle) * radius,
            cos(i * angle) * radius + y,
        )
        for i in range(12)
    ]

    radius *= 0.4

    x_sign = (
        ( radius, y + radius),
        (-radius, y - radius),
        (-radius, y + radius),
        ( radius, y - radius),
    )

    return (*_co_pairs_cyclic(circle), *x_sign)


@lru_cache(maxsize=1)
def _icon_warning(radius: float) -> tuple[tuple[float, float], ...]:
    radius *= 1.1
    y = -radius / 4

    tri = (
        (0.0, y + radius * 2),
        (0.0 - radius, y),
        (0.0 + radius, y),
    )

    y = -y

    exclamation = (
        (0.0, y + radius * 0.9),
        (0.0, y + radius * 0.2),
        (0.0, y),
        (0.0, y - radius * 0.2),
    )

    return (*_co_pairs_cyclic(tri), *exclamation)


# Utils
# -------------------------------------


def _co_pairs_cyclic(a: Iterable) -> Iterator[tuple[float, float]]:
    b = itertools.cycle(a)
    next(b)

    for co1, co2 in zip(a, b):
        yield co1
        yield co2


def _co_pairs(x: Iterable) -> Iterator[tuple[float, float]]:
    a, b = itertools.tee(x)
    next(b, None)

    for co1, co2 in zip(a, b):
        yield co1
        yield co2


def _fmt_detailed(seq: Iterable) -> Iterator[tuple[int | None, str]]:
    if mod_update.state.update_available:
        yield None, _t("Update {} is available").format(mod_update.state.update_version)

    for x in seq:
        yield x.type, _t(x.title)
