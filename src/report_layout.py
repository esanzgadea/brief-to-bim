
from pathlib import Path
import json

from schema import Project
from evaluate_layout import evaluate_layout


# 1. Load the architectural programme

programme_text = Path("data/programme.json").read_text(encoding="utf-8")
project = Project.model_validate_json(programme_text)


# 2. Load the best generated layout

layout_text = Path("outputs/best_layout.json").read_text(encoding="utf-8")
layout = json.loads(layout_text)


# 3. Evaluate the selected layout

evaluation = evaluate_layout(project, layout)


# 4. Organise results by space ID

proportions = {
    result["id"]: result
    for result in evaluation["proportions"]
}

daylight = {
    result["id"]: result
    for result in evaluation["daylight"]
}


# 5. Build a structured report

report = {
    "project": project.name,
    "selected_seed": layout["seed"],

    "scores": {
        "relationships": evaluation["relationship_score"],
        "relationships_max": evaluation["relationship_max_score"],
        "proportions": evaluation["proportion_score"],
        "daylight": evaluation["daylight_score"]
    },

    "relationships": evaluation["relationships"],

    "spaces": [
        {
            "id": space.id,
            "name": space.name,
            "area_m2": space.target_area_m2,
            "aspect_ratio": round(proportions[space.id]["aspect_ratio"], 2),
            "proportion_score": proportions[space.id]["score"],
            "daylight_requirement": space.daylight.value,
            "touches_facade": daylight[space.id]["has_facade"]
        }
        for space in project.spaces
    ]
}


# 6. Save the report

output_path = Path("outputs/best_layout_report.json")

output_path.write_text(
    json.dumps(report, indent=2),
    encoding="utf-8"
)


# 7. Print a short summary

print(f'Selected seed: {report["selected_seed"]}')

print("\nSPACE EVALUATION:\n")

for space in report["spaces"]:
    print(
        f'{space["name"]:20s} | '
        f'Ratio: {space["aspect_ratio"]:5.2f} | '
        f'Proportion score: {space["proportion_score"]}/3 | '
        f'Facade: {space["touches_facade"]}'
    )

print(f"\nReport saved to: {output_path}")
