# -*- coding: utf-8 -*-
"""Brief-to-BIM: Revit walls with open corridor junctions.

Reads outputs/best_layout.json. Uses existing Basic Wall types whose
Function is Interior or Exterior. Run in a clean Revit floor-plan view.
"""
import os
import json
from pyrevit import revit, DB, forms


doc = revit.doc
view = revit.active_view
if view.ViewType != DB.ViewType.FloorPlan:
    forms.alert("Please open a floor plan.", exitscript=True)
level = view.GenLevel

project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", ".."
))
file_path = os.path.join(project_root, "outputs", "best_layout.json")
with open(file_path, "r") as file:
    layout = json.load(file)

rooms = layout["rooms"]


def to_revit(metres):
    return DB.UnitUtils.ConvertToInternalUnits(float(metres), DB.UnitTypeId.Meters)


def to_metres(feet):
    return DB.UnitUtils.ConvertFromInternalUnits(float(feet), DB.UnitTypeId.Meters)


# Use existing types: never silently replace an exterior wall with an interior one.
wall_types = [wt for wt in DB.FilteredElementCollector(doc).OfClass(DB.WallType)
              if wt.Kind == DB.WallKind.Basic]
inside = [wt for wt in wall_types if wt.Function == DB.WallFunction.Interior]
outside = [wt for wt in wall_types if wt.Function == DB.WallFunction.Exterior]
if not inside or not outside:
    forms.alert("Load/configure at least one Basic Wall type with Function=Interior "
                "and one with Function=Exterior.", exitscript=True)

interior_type = min(inside, key=lambda wt: abs(wt.Width - to_revit(0.12)))
exterior_type = min(outside, key=lambda wt: abs(wt.Width - to_revit(0.25)))
if interior_type.Width >= exterior_type.Width:
    forms.alert("Interior wall type must be thinner than exterior wall type.",
                exitscript=True)


# Split the shared rectangle edges at ALL partition vertices. At the midpoint
# of each segment, look up which spaces are on both sides. If both are corridors,
# the line is an opening, not a wall. This works whatever side owns corridor 2.
TOL = 1e-7
xs = sorted(set(round(c, 6) for r in rooms for c in (r["x"], r["x"] + r["width"])))
ys = sorted(set(round(c, 6) for r in rooms for c in (r["y"], r["y"] + r["height"])))


def room_at(x, y):
    for r in rooms:
        if (r["x"] + TOL < x < r["x"] + r["width"] - TOL
                and r["y"] + TOL < y < r["y"] + r["height"] - TOL):
            return r
    return None


def is_corridor(room):
    return room is not None and (
        room.get("kind") == "circulation"
        or room.get("id", "").startswith("corridor_")
    )


def wall_kind(a, b):
    if a is None and b is None:
        return None
    if a is not None and b is not None:
        if a["id"] == b["id"] or (is_corridor(a) and is_corridor(b)):
            return None
        return "interior"
    return "exterior"


min_dx = min(xs[i + 1] - xs[i] for i in range(len(xs) - 1))
min_dy = min(ys[i + 1] - ys[i] for i in range(len(ys) - 1))
dx = min(0.0001, min_dx / 4)
dy = min(0.0001, min_dy / 4)

# A segment is (direction, fixed coordinate, start, end, classification).
raw = []
for x in xs:
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        mid = (y0 + y1) / 2
        kind = wall_kind(room_at(x - dx, mid), room_at(x + dx, mid))
        if kind:
            raw.append(("V", x, y0, y1, kind))

for y in ys:
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        mid = (x0 + x1) / 2
        kind = wall_kind(room_at(mid, y - dy), room_at(mid, y + dy))
        if kind:
            raw.append(("H", y, x0, x1, kind))

# Merge consecutive same-type collinear fragments into longer native Revit walls.
raw.sort(key=lambda s: (s[0], s[1], s[4], s[2]))
segments = []
for axis, fixed, start, end, kind in raw:
    if (segments and segments[-1][0] == axis
            and segments[-1][1] == fixed and segments[-1][4] == kind
            and abs(segments[-1][3] - start) < 1e-6):
        prev = segments.pop()
        segments.append((axis, fixed, prev[2], end, kind))
    else:
        segments.append((axis, fixed, start, end, kind))


z = level.Elevation

def xyz(x, y):
    return DB.XYZ(to_revit(x), to_revit(y), z)

counts = {"interior": 0, "exterior": 0}
with revit.Transaction("Brief-to-BIM Create Walls"):
    for axis, fixed, start, end, kind in segments:
        if axis == "V":
            curve = DB.Line.CreateBound(xyz(fixed, start), xyz(fixed, end))
        else:
            curve = DB.Line.CreateBound(xyz(start, fixed), xyz(end, fixed))
        wt = exterior_type if kind == "exterior" else interior_type
        DB.Wall.Create(doc, curve, wt.Id, level.Id,
                       to_revit(3.0), 0.0, False, False)
        counts[kind] += 1

forms.alert(
    "Created {} exterior and {} interior walls.\n"
    "Corridor-to-corridor boundaries are OPEN.\n"
    "Exterior thickness: {:.0f} mm\n"
    "Interior thickness: {:.0f} mm".format(
        counts["exterior"],
        counts["interior"],
        to_metres(exterior_type.Width) * 1000,
        to_metres(interior_type.Width) * 1000
    ),
    title="Brief-to-BIM"
)
