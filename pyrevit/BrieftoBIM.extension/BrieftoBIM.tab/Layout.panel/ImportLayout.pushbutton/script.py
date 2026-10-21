
# -*- coding: utf-8 -*-

import os
import json

from pyrevit import revit, DB, forms


# 1. ACCESS THE ACTIVE REVIT DOCUMENT

doc = revit.doc
view = revit.active_view

if view.ViewType != DB.ViewType.FloorPlan:
    forms.alert(
        "Please open a floor plan view.",
        exitscript=True
    )


# 2. LOCATE AND READ THE JSON FILE

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


# 3. CONVERT UNITS AND COORDINATES

def to_revit(value):
    return DB.UnitUtils.ConvertToInternalUnits(
        float(value),
        DB.UnitTypeId.Meters
    )


level_z = view.GenLevel.Elevation

def point(x, y):
    return DB.XYZ(
        to_revit(x),
        to_revit(y),
        level_z
    )


# 4. CREATE MODEL LINES

created = 0

with revit.Transaction("Brief-to-BIM Import Layout"):

    plane = DB.Plane.CreateByNormalAndOrigin(
        DB.XYZ.BasisZ,
        DB.XYZ(0, 0, level_z)
    )

    sketch_plane = DB.SketchPlane.Create(doc, plane)

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

            line = DB.Line.CreateBound(start, end)

            doc.Create.NewModelCurve(
                line,
                sketch_plane
            )

            created += 1


# 5. DISPLAY RESULT

forms.alert(
    "Imported {} spaces\nCreated {} model lines\nSeed {}".format(
        len(rooms),
        created,
        layout["seed"]
    ),
    title="Brief-to-BIM"
)
