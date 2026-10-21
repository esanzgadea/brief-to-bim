
# -*- coding: utf-8 -*-

import os
import json

from pyrevit import revit, DB, forms


# 1. ACCESS REVIT DOCUMENT

doc = revit.doc
view = revit.active_view

if view.ViewType != DB.ViewType.FloorPlan:
    forms.alert(
        "Please open a floor plan.",
        exitscript=True
    )

level = view.GenLevel


# 2. READ LAYOUT JSON

project_root = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "..", ".."
    )
)

file_path = os.path.join(
    project_root,
    "outputs",
    "best_layout.json"
)

with open(file_path, "r") as file:
    layout = json.load(file)

rooms = layout["rooms"]
building_width = layout["building_width"]
building_height = layout["building_height"]


# 3. SELECT A WALL TYPE FROM REVIT

wall_types = [
    wt for wt in DB.FilteredElementCollector(doc)
    .OfClass(DB.WallType)
    if wt.Kind == DB.WallKind.Basic
]

if not wall_types:
    forms.alert("No basic wall types found.", exitscript=True)

wall_type = wall_types[0]


# 4. UNITS AND GEOMETRY

def to_revit(value):
    return DB.UnitUtils.ConvertToInternalUnits(
        float(value),
        DB.UnitTypeId.Meters
    )


level_z = level.Elevation

def point(x, y):
    return DB.XYZ(
        to_revit(x),
        to_revit(y),
        level_z
    )


wall_height = to_revit(3.0)
created = 0


# 5. CREATE WALLS

with revit.Transaction("Brief-to-BIM Create Walls"):

    for room in rooms:

        x = room["x"]
        y = room["y"]
        w = room["width"]
        h = room["height"]

        segments = [
            (point(x, y), point(x, y + h)),
            (point(x, y), point(x + w, y))
        ]

        if abs(x + w - building_width) < 1e-6:
            segments.append((
                point(x + w, y),
                point(x + w, y + h)
            ))

        if abs(y + h - building_height) < 1e-6:
            segments.append((
                point(x, y + h),
                point(x + w, y + h)
            ))

        for start, end in segments:

            curve = DB.Line.CreateBound(start, end)

            wall = DB.Wall.Create(
                doc,
                curve,
                wall_type.Id,
                level.Id,
                wall_height,
                0.0,
                False,
                False
            )

            created += 1


# 6. CONFIRM RESULT

forms.alert(
    "Created {} BIM walls\nHeight: 3.0 m\nSeed: {}".format(
        created,
        layout["seed"]
    ),
    title="Brief-to-BIM"
)
