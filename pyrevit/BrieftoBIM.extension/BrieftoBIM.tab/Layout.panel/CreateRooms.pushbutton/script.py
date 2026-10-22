
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


# 2. READ THE GENERATED LAYOUT

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

# Exclude the unallocated space
spaces = [
    room for room in layout["rooms"]
    if room["id"] not in ("unallocated", "corridor_secondary")
]


# 3. UNIT CONVERSION

def to_revit(value):
    return DB.UnitUtils.ConvertToInternalUnits(
        float(value),
        DB.UnitTypeId.Meters
    )


def to_m2(value):
    return DB.UnitUtils.ConvertFromInternalUnits(
        value,
        DB.UnitTypeId.SquareMeters
    )


# 4. CHECK EXISTING ROOMS AND TAG TYPES

existing_numbers = {
    room.Number
    for room in DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_Rooms)
    .WhereElementIsNotElementType()
}

numbers = [
    "B2B-{:02d}".format(i)
    for i in range(1, len(spaces) + 1)
]

if any(number in existing_numbers for number in numbers):
    forms.alert(
        "Brief-to-BIM rooms already exist. "
        "Delete them before running again.",
        exitscript=True
    )

tag_types = list(
    DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_RoomTags)
    .WhereElementIsElementType()
)

if not tag_types:
    forms.alert(
        "No Room Tag family loaded in this project.",
        exitscript=True
    )


# 5. CREATE ROOMS AND TAGS

results = []

with revit.Transaction("Brief-to-BIM Create Rooms"):

    for index, space in enumerate(spaces, start=1):

        # Calculate room centre in metres
        cx = space["x"] + space["width"] / 2
        cy = space["y"] + space["height"] / 2

        # Convert to Revit internal units
        location = DB.UV(
            to_revit(cx),
            to_revit(cy)
        )

        # Create BIM Room
        room = doc.Create.NewRoom(level, location)

        if room is None:
            raise Exception(
                "Room creation failed: " + space["name"]
            )

        # Assign BIM parameters
        room.Name = space["name"]
        room.Number = "B2B-{:02d}".format(index)

        # Update Revit's geometry and room calculations
        doc.Regenerate()

        # Read actual BIM area
        actual_area = to_m2(room.Area)
        target_area = space["area"]

        if space["id"] == "corridor_main":
            target_area = sum(
                r["area"] for r in layout["rooms"]
                if r.get("kind") == "circulation"
            )

        if actual_area <= 0:
            raise Exception(
                "Room is not enclosed: " + space["name"]
            )

        # Create annotation in active plan view
        tag = doc.Create.NewRoomTag(
            DB.LinkElementId(room.Id),
            location,
            view.Id
        )

        if tag is None:
            raise Exception(
                "Could not tag: " + space["name"]
            )

        results.append({
            "name": space["name"],
            "target": target_area,
            "actual": actual_area
        })


# 6. PRINT AREA COMPARISON

print("\nBRIEF-TO-BIM | ROOM AREA COMPARISON\n")

total_target = 0
total_actual = 0

for result in results:

    difference = result["actual"] - result["target"]

    total_target += result["target"]
    total_actual += result["actual"]

    print(
        "{:<22} Target: {:6.2f} m2 | "
        "Revit: {:6.2f} m2 | "
        "Diff: {:+6.2f} m2".format(
            result["name"],
            result["target"],
            result["actual"],
            difference
        )
    )


print("\nTOTAL TARGET: {:.2f} m2".format(total_target))
print("TOTAL REVIT:  {:.2f} m2".format(total_actual))


# 7. CONFIRM RESULT

forms.alert(
    "Created {} BIM Rooms and Room Tags\n"
    "Seed {}".format(
        len(results),
        layout["seed"]
    ),
    title="Brief-to-BIM"
)
