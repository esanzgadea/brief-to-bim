
from pathlib import Path
import json
import math

from schema import Project

TOLERANCE = 1e-6


# 1. GEOMETRIC HELPERS

def get_bounds(room):
    left = room["x"]
    right = room["x"] + room["width"]
    bottom = room["y"]
    top = room["y"] + room["height"]

    return left, right, bottom, top


def overlap_1d(a_min, a_max, b_min, b_max):
    return max(0, min(a_max, b_max) - max(a_min, b_min))


def are_adjacent(room_a, room_b):

    left_a, right_a, bottom_a, top_a = get_bounds(room_a)
    left_b, right_b, bottom_b, top_b = get_bounds(room_b)

    vertical_touch = (
        abs(right_a - left_b) < TOLERANCE
        or abs(right_b - left_a) < TOLERANCE
    )

    vertical_overlap = overlap_1d(
        bottom_a, top_a, bottom_b, top_b
    )

    horizontal_touch = (
        abs(top_a - bottom_b) < TOLERANCE
        or abs(top_b - bottom_a) < TOLERANCE
    )

    horizontal_overlap = overlap_1d(
        left_a, right_a, left_b, right_b
    )

    return (
        (vertical_touch and vertical_overlap > TOLERANCE)
        or
        (horizontal_touch and horizontal_overlap > TOLERANCE)
    )


def centroid_distance(room_a, room_b):

    ax = room_a["x"] + room_a["width"] / 2
    ay = room_a["y"] + room_a["height"] / 2

    bx = room_b["x"] + room_b["width"] / 2
    by = room_b["y"] + room_b["height"] / 2

    return math.dist((ax, ay), (bx, by))


def are_near(room_a, room_b, threshold=6.0):
    return centroid_distance(room_a, room_b) <= threshold

def aspect_ratio(room):
    width = room["width"]
    height = room["height"]
    return max(width, height) / min(width, height)


def proportion_score_for_room(room):
    ratio = aspect_ratio(room)

    # Simple stepped scoring
    if ratio <= 1.8:
        return 3
    elif ratio <= 2.5:
        return 2
    elif ratio <= 4.0:
        return 1
    else:
        return 0


def touches_facade(room, building_width, building_height):
    left, right, bottom, top = get_bounds(room)

    return (
        abs(left - 0) < TOLERANCE
        or abs(bottom - 0) < TOLERANCE
        or abs(right - building_width) < TOLERANCE
        or abs(top - building_height) < TOLERANCE
    )

# 2. REUSABLE EVALUATION FUNCTION

def evaluate_layout(project, layout_data):

    rooms = layout_data["rooms"]
    building_width = layout_data["building_width"]
    building_height = layout_data["building_height"]

    room_by_id = {
        room["id"]: room
        for room in rooms
    }

    # --------------------------------------------------
    # 1. RELATIONSHIP SCORE
    # --------------------------------------------------

    relationship_score = 0
    relationship_max_score = 0
    relationship_results = []

    for relationship in project.relationships:

        room_a = room_by_id[relationship.space_a]
        room_b = room_by_id[relationship.space_b]

        relationship_type = relationship.type.value
        priority = relationship.priority

        relationship_max_score += priority

        adjacent = are_adjacent(room_a, room_b)
        near = are_near(room_a, room_b)

        if relationship_type == "adjacent":
            satisfied = adjacent

        elif relationship_type == "near":
            satisfied = adjacent or near

        elif relationship_type == "separate":
            satisfied = not adjacent and not near

        else:
            satisfied = False

        if satisfied:
            relationship_score += priority

        relationship_results.append({
            "space_a": relationship.space_a,
            "space_b": relationship.space_b,
            "type": relationship_type,
            "satisfied": satisfied,
            "priority": priority
        })

    relationship_success_rate = (
        100 * relationship_score / relationship_max_score
        if relationship_max_score > 0
        else 0
    )

    # --------------------------------------------------
    # 2. PROPORTION SCORE
    # --------------------------------------------------

    proportion_score = 0
    proportion_results = []

    for room in rooms:
        if room["id"] == "unallocated":
            continue

        room_score = proportion_score_for_room(room)
        proportion_score += room_score

        proportion_results.append({
            "id": room["id"],
            "name": room["name"],
            "aspect_ratio": aspect_ratio(room),
            "score": room_score
        })

    # --------------------------------------------------
    # 3. DAYLIGHT SCORE
    # --------------------------------------------------

    daylight_score = 0
    daylight_results = []

    for space in project.spaces:
        room = room_by_id[space.id]
        has_facade = touches_facade(
            room,
            building_width,
            building_height
        )

        room_score = 0

        if space.daylight.value == "high":
            room_score = 2 if has_facade else 0

        elif space.daylight.value == "medium":
            room_score = 1 if has_facade else 0

        elif space.daylight.value == "low":
            room_score = 1

        daylight_score += room_score

        daylight_results.append({
            "id": space.id,
            "name": space.name,
            "daylight": space.daylight.value,
            "has_facade": has_facade,
            "score": room_score
        })

    # --------------------------------------------------
    # 4. TOTAL SCORE
    # --------------------------------------------------

    total_score = (
        relationship_score * 100
        + proportion_score * 10
        + daylight_score
    )

    return {
        "relationship_score": relationship_score,
        "relationship_max_score": relationship_max_score,
        "relationship_success_rate": relationship_success_rate,

        "proportion_score": proportion_score,
        "daylight_score": daylight_score,
        "total_score": total_score,

        "relationships": relationship_results,
        "proportions": proportion_results,
        "daylight": daylight_results
    }

# 3. RUN DIRECTLY FOR TESTING

if __name__ == "__main__":

    programme_text = Path(
        "data/programme.json"
    ).read_text(encoding="utf-8")

    project = Project.model_validate_json(programme_text)

    layout_text = Path(
        "outputs/layout.json"
    ).read_text(encoding="utf-8")

    layout_data = json.loads(layout_text)

    result = evaluate_layout(project, layout_data)

    for relationship in result["relationships"]:
        print(relationship)

    print(
        f'\nScore: {result["score"]}/{result["max_score"]}'
    )
    print(
        f'Success rate: {result["success_rate"]:.1f}%'
    )
