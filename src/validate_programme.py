from pathlib import Path
from schema import Project

# Load the existing programme
json_text = Path("data/programme.json").read_text(encoding="utf-8")
project = Project.model_validate_json(json_text)

# Collect space IDs
space_ids = [space.id for space in project.spaces]

errors = []

if len(space_ids) != len(set(space_ids)):
    errors.append("Duplicate space IDs")

for relationship in project.relationships:
    if relationship.space_a not in space_ids:
        errors.append(f"Unknown space: {relationship.space_a}")

    if relationship.space_b not in space_ids:
        errors.append(f"Unknown space: {relationship.space_b}")

if errors:
    raise ValueError("\n".join(errors))

# Check areas
total_spaces_area = sum(space.target_area_m2 for space in project.spaces)
remaining_area = project.total_area_m2 - total_spaces_area

print(f"Project area: {project.total_area_m2} m²")
print(f"Programmed area: {total_spaces_area} m²")
print(f"Remaining area: {remaining_area} m²")