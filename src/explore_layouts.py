
from pathlib import Path
import json

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from schema import Project
from layout_engine import generate_layout
from evaluate_layout import evaluate_layout


# 1. LOAD PROGRAMME

json_text = Path("data/programme.json").read_text(
    encoding="utf-8"
)

project = Project.model_validate_json(json_text)


# 2. GENERATE AND EVALUATE ALTERNATIVES

alternatives = []

for seed in range(100):

    layout = generate_layout(project, seed=seed)

    evaluation = evaluate_layout(project, layout)

    alternatives.append({
        "seed": seed,
        "layout": layout,
        "evaluation": evaluation
    })


# 3. SORT ALTERNATIVES BY SCORE

alternatives.sort(
    key=lambda option: (
        option["evaluation"]["relationship_score"],
        option["evaluation"]["proportion_score"],
        option["evaluation"]["daylight_score"]
    ),
    reverse=True
)


# 4. PRINT THE BEST RESULTS

print("\nTOP 10 ALTERNATIVES:\n")

for option in alternatives[:10]:

    relationship_score = option["evaluation"]["relationship_score"]
    relationship_max = option["evaluation"]["relationship_max_score"]
    total_score = option["evaluation"]["total_score"]
    proportion_score = option["evaluation"]["proportion_score"]
    daylight_score = option["evaluation"]["daylight_score"]

    print(
        f'Seed {option["seed"]:3d} | '
        f'Relationships: {relationship_score}/{relationship_max} | '
        f'Proportion: {proportion_score} | '
        f'Daylight: {daylight_score} | '
        f'Total: {total_score}'
    )


# 5. SAVE THE BEST LAYOUT

best = alternatives[0]

Path("outputs/best_layout.json").write_text(
    json.dumps(best["layout"], indent=2),
    encoding="utf-8"
)


# 6. DRAW THE SIX BEST ALTERNATIVES

fig, axes = plt.subplots(2, 3, figsize=(15, 10))

for ax, option in zip(axes.flat, alternatives[:6]):

    layout = option["layout"]

    for room in layout["rooms"]:

        rect = Rectangle(
            (room["x"], room["y"]),
            room["width"],
            room["height"],
            facecolor="#DCE8ED",
            edgecolor="#34495E",
            linewidth=1
        )

        ax.add_patch(rect)

        ax.text(
            room["x"] + room["width"] / 2,
            room["y"] + room["height"] / 2,
            room["name"],
            ha="center",
            va="center",
            fontsize=6
        )

    ax.set_xlim(0, layout["building_width"])
    ax.set_ylim(0, layout["building_height"])
    ax.set_aspect("equal")
    ax.axis("off")

    relationship_score = option["evaluation"]["relationship_score"]
    relationship_max = option["evaluation"]["relationship_max_score"]
    total_score = option["evaluation"]["total_score"]

    ax.set_title(
        f'Seed {option["seed"]} — R {relationship_score}/{relationship_max} — T {total_score}',
        fontsize=11
    )


fig.suptitle("Brief-to-BIM — Layout Exploration", fontsize=18)

plt.tight_layout()

plt.savefig(
    "outputs/layout_exploration.png",
    dpi=250,
    bbox_inches="tight"
)

plt.show()
