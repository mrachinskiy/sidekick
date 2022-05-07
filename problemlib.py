# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2022 Mikhail Rachinskiy

from typing import NamedTuple


TYPE_ERROR = 1
TYPE_WARN = 2

# Object
ID_OB_SCALE = 101
ID_OB_EMPTY = 102

# Relations
ID_MOD_ORDER = 201
ID_CYCLIC_DEP = 202

# Object Data
ID_CURVE_RADIUS = 301
ID_CURVE_ORDER = 302
ID_CURVE_RESOLUTION = 303

# Scene
ID_COLLECTION_NAME = 401
ID_COLLECTION_VISIBILITY = 402


class Problem(NamedTuple):
    code: int
    type: int
    title: str
    desc: str
    select: bool = True


ObjectScale = Problem(
    ID_OB_SCALE,
    TYPE_ERROR,
    "Scaled object",
    (
        "Object scaling could lead to unexpected results when using certain tools and modifiers."
        "\n\nRecommendation: if you did not set object scale on purpose use Object > Apply > Scale."
    ),
)

ObjectEmpty = Problem(
    ID_OB_EMPTY,
    TYPE_WARN,
    "Empty object",
    (
        "Mesh or curve object missing object data."
        "\n\nRecommendation: delete empty objects."
    ),
)

ModOrder = Problem(
    ID_MOD_ORDER,
    TYPE_ERROR,
    "Modifier order is incorrect",
    (
        "Generally Subdivision modifier should be placed before deform modifiers. Example:"
        "\n* Mirror"
        "\n* Subdivision"
        "\n* Lattice"
        "\n* Curve"
        "\n\nRecommendation: place Subdivision modifier before deform modifiers, "
        "unless you did it on purpose to achieve specific result."
    ),
)

CyclicDep = Problem(
    ID_CYCLIC_DEP,
    TYPE_ERROR,
    "Cyclic dependency",
    (
        "Using the same object as a target for Shrinkwrap and Boolean modifiers creates cyclic dependency."
        "\n\nRecommendation: use a duplicate object without Boolean modifier as a target in Shrinkwrap modifier."
    ),
)

CurveRadius = Problem(
    ID_CURVE_RADIUS,
    TYPE_ERROR,
    "Curve Radius deformation",
    (
        "Curve Radius scales objects deformed by Curve modifier."
        "\n\nRecommendation: disable curve Radius property, unless you are using it on purpose."
    ),
)

CurveOrder = Problem(
    ID_CURVE_ORDER,
    TYPE_ERROR,
    "Curve low Order",
    (
        "Low Order property makes curve shape angular."
        "\n\nRecommendation: set Object Data > Active Spline > Order U property to 5, "
        "if you need angular curve, then you better off using Bezier curves."
    ),
)

CurveResolution = Problem(
    ID_CURVE_RESOLUTION,
    TYPE_ERROR,
    "Curve low Resolution",
    (
        "Low Resolution property makes deformed object look low poly regardless of its polycount."
        "\n\nRecommendation: set Object Data > Shape > Resolution Preview U property to a greater value."
    ),
)

CollectionName = Problem(
    ID_COLLECTION_NAME,
    TYPE_WARN,
    "Collection uses default name",
    (
        "Default collection names make it difficult to understand scene hierarchy for other people and yourself."
        "\n\nRecommendation: give descriptive names to all collections."
    ),
    False,
)

CollectionVisibility = Problem(
    ID_COLLECTION_VISIBILITY,
    TYPE_ERROR,
    "Collection visibility",
    (
        "Gems from hidden collections will appear in Design Report and Gem Map, "
        "this happens when collection is hidden with Hide in Viewport (eye icon)."
        "\n\nRecommendation: instead use Disable in Viewports (display icon) "
        "or Exclude from View Layer (checkbox)."
    ),
    False,
)


coll = {
    ObjectScale.code: ObjectScale,
    ObjectEmpty.code: ObjectEmpty,
    ModOrder.code: ModOrder,
    CyclicDep.code: CyclicDep,
    CurveRadius.code: CurveRadius,
    CurveOrder.code: CurveOrder,
    CurveResolution.code: CurveResolution,
    CollectionName.code: CollectionName,
    CollectionVisibility.code: CollectionVisibility,
}
