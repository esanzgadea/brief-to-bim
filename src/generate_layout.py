
from pathlib import Path
import json
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import random

from schema import Project


# 1. LOAD PROJECT DATA

json_text = Path("data/programme.json").read_text(encoding="utf-8")
project = Project.model_validate_json(json_text)



# Generate the layout using our new module
from layout_engine import generate_layout

layout_data = generate_layout(
    project,
    seed=1,
    building_width=14.0
)

layout = layout_data["rooms"]
building_width = layout_data["building_width"]
building_height = layout_data["building_height"]


# 5. SAVE LAYOUT

Path("outputs").mkdir(exist_ok=True)

output = {
    "building_width": building_width,
    "building_height": building_height,
    "rooms": layout
}

Path("outputs/layout.json").write_text(
    json.dumps(output, indent=2),
    encoding="utf-8"
)


# 6. DRAW THE PLAN

fig, ax = plt.subplots(figsize=(11, 8))

for room in layout:
    rectangle = Rectangle(
        (room["x"], room["y"]),
        room["width"],
        room["height"],
        facecolor="#DCE8ED",
        edgecolor="#34495E",
        linewidth=1.5
    )

    ax.add_patch(rectangle)

    ax.text(
        room["x"] + room["width"] / 2,
        room["y"] + room["height"] / 2,
        f'{room["name"]}\n{room["area"]:g} m²',
        ha="center",
        va="center",
        fontsize=8
    )

ax.set_xlim(0, building_width)
ax.set_ylim(0, building_height)
ax.set_aspect("equal")
ax.set_title("Generated Layout — BSP")
ax.axis("off")

plt.savefig(
    "outputs/layout.png",
    dpi=250,
    bbox_inches="tight"
)

plt.show()
