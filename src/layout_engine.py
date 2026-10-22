"""BSP layout with circulation strips at its first two partitions.

Room target areas are preserved by enlarging the rectangular envelope.
All later cuts use the original recursive BSP algorithm.
"""

import random


def generate_layout(
    project,
    seed=1,
    building_width=14.0,
    main_corridor_width=1.8,
    secondary_corridor_width=1.2,
):
    if building_width <= main_corridor_width or main_corridor_width <= 0:
        raise ValueError("Building width must exceed the main corridor width")

    if secondary_corridor_width <= 0:
        raise ValueError("Secondary corridor width must be positive")

    spaces = [
        {"id": space.id, "name": space.name, "area": space.target_area_m2}
        for space in project.spaces
    ]
    remaining_area = project.total_area_m2 - sum(s["area"] for s in spaces)

    if remaining_area < -1e-6:
        raise ValueError("Programmed area exceeds building area")
    if remaining_area > 1e-6:
        spaces.append({
            "id": "unallocated", "name": "Unallocated", "area": remaining_area
        })

    random.Random(seed).shuffle(spaces)
    layout = []

    def area(items):
        return sum(item["area"] for item in items)

    def split_items(items):
        """Same area-balanced contiguous grouping as the original BSP."""
        midpoint = min(
            range(1, len(items)),
            key=lambda i: abs(area(items[:i]) - area(items) / 2),
        )
        return items[:midpoint], items[midpoint:]

    def partition(items, x, y, width, height):
        """Original BSP, unchanged for all remaining partitions."""
        if len(items) == 1:
            room = items[0].copy()
            room.update({"x": x, "y": y, "width": width, "height": height})
            layout.append(room)
            return

        group_a, group_b = split_items(items)
        fraction = area(group_a) / area(items)

        if width >= height:
            split = width * fraction
            partition(group_a, x, y, split, height)
            partition(group_b, x + split, y, width - split, height)
        else:
            split = height * fraction
            partition(group_a, x, y, width, split)
            partition(group_b, x, y + split, width, height - split)

    if len(spaces) < 2:
        building_height = project.total_area_m2 / building_width
        partition(spaces, 0, 0, building_width, building_height)
        return {
            "seed": seed,
            "building_width": building_width,
            "building_height": building_height,
            "rooms": layout,
        }

    # First original BSP split, replaced by a main circulation strip.
    groups = list(split_items(spaces))
    group_areas = [area(group) for group in groups]
    eligible = [i for i in range(2) if len(groups[i]) >= 2]
    secondary_owner = max(
        eligible, key=lambda i: (len(groups[i]), group_areas[i])
    ) if eligible else None
    secondary_gap = secondary_corridor_width if secondary_owner is not None else 0.0

    # Use the same orientation rule as the original first BSP split.
    vertical_main = building_width >= project.total_area_m2 / building_width

    if vertical_main:
        # Keep building width fixed and solve for the additional building height
        # needed to preserve every room's target area.
        def required_width(height):
            widths = [                
                group_areas[i] / (height - (secondary_gap if i == secondary_owner else 0.0))
                for i in range(2)
            ]
            return sum(widths) + main_corridor_width

        low = secondary_gap + 1e-6
        high = max(project.total_area_m2 / (building_width - main_corridor_width) * 2, low * 2)
        while required_width(high) > building_width:
            high *= 2
        for _ in range(80):
            mid = (low + high) / 2
            if required_width(mid) > building_width:
                low = mid
            else:
                high = mid
        building_height = high
        first_sizes = [
            group_areas[i] / (building_height - (secondary_gap if i == secondary_owner else 0.0))
            for i in range(2)
        ]
        group_rects = [
            (0.0, 0.0, first_sizes[0], building_height),
            (first_sizes[0] + main_corridor_width, 0.0, first_sizes[1], building_height),
        ]
        main = {
            "id": "corridor_main", "name": "Main Corridor", "kind": "circulation",
            "x": first_sizes[0], "y": 0.0,
            "width": main_corridor_width, "height": building_height,
            "area": main_corridor_width * building_height,
        }
    else:
        # Horizontal first split: building width stays fixed, height grows.
        first_sizes = [
            group_areas[i] / (building_width - (secondary_gap if i == secondary_owner else 0.0))
            for i in range(2)
        ]
        building_height = sum(first_sizes) + main_corridor_width
        group_rects = [
            (0.0, 0.0, building_width, first_sizes[0]),
            (0.0, first_sizes[0] + main_corridor_width, building_width, first_sizes[1]),
        ]
        main = {
            "id": "corridor_main", "name": "Main Corridor", "kind": "circulation",
            "x": 0.0, "y": first_sizes[0],
            "width": building_width, "height": main_corridor_width,
            "area": building_width * main_corridor_width,
        }

    for i, (items, (x, y, width, height)) in enumerate(zip(groups, group_rects)):
        if i != secondary_owner:
            partition(items, x, y, width, height)
            continue

        # Second BSP split: reserve a narrower circulation strip in one branch.
        group_a, group_b = split_items(items)
        fraction = area(group_a) / area(items)
        if vertical_main:
            # First cut vertical, second cut horizontal (perpendicular branch).
            available_height = height - secondary_gap
            cut = available_height * fraction
            partition(group_a, x, y, width, cut)
            partition(group_b, x, y + cut + secondary_gap, width, available_height - cut)
            secondary = {
                "id": "corridor_secondary", "name": "Secondary Corridor",
                "kind": "circulation", "x": x, "y": y + cut,
                "width": width, "height": secondary_gap,
                "area": width * secondary_gap,
            }
        else:
            # First cut horizontal, second cut vertical.
            available_width = width - secondary_gap
            cut = available_width * fraction
            partition(group_a, x, y, cut, height)
            partition(group_b, x + cut + secondary_gap, y, available_width - cut, height)
            secondary = {
                "id": "corridor_secondary", "name": "Secondary Corridor",
                "kind": "circulation", "x": x + cut, "y": y,
                "width": secondary_gap, "height": height,
                "area": height * secondary_gap,
            }

    layout.append(main)
    if secondary_owner is not None:
        layout.append(secondary)

    return {
        "seed": seed,
        "building_width": building_width,
        "building_height": building_height,
        "rooms": layout,
    }

