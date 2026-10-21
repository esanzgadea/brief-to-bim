
import random


def generate_layout(project, seed=1, building_width=14.0):

    # 1. Building dimensions

    building_height = project.total_area_m2 / building_width

    # 2. Prepare spaces

    spaces = [
        {
            "id": space.id,
            "name": space.name,
            "area": space.target_area_m2
        }
        for space in project.spaces
    ]

    remaining_area = project.total_area_m2 - sum(
        space["area"] for space in spaces
    )

    if remaining_area < -0.000001:
        raise ValueError("Programmed area exceeds building area")

    if remaining_area > 0.000001:
        spaces.append({
            "id": "unallocated",
            "name": "Unallocated",
            "area": remaining_area
        })

    # 3. Randomise the order using a reproducible seed

    random.Random(seed).shuffle(spaces)

    # 4. Recursive BSP algorithm

    layout = []

    def partition(items, x, y, width, height):

        if len(items) == 1:
            room = items[0].copy()

            room.update({
                "x": x,
                "y": y,
                "width": width,
                "height": height
            })

            layout.append(room)
            return

        total_area = sum(item["area"] for item in items)

        split_index = min(
            range(1, len(items)),
            key=lambda i: abs(
                sum(item["area"] for item in items[:i])
                - total_area / 2
            )
        )

        group_a = items[:split_index]
        group_b = items[split_index:]

        fraction = sum(item["area"] for item in group_a) / total_area

        if width >= height:
            split = width * fraction

            partition(group_a, x, y, split, height)
            partition(group_b, x + split, y, width - split, height)

        else:
            split = height * fraction

            partition(group_a, x, y, width, split)
            partition(group_b, x, y + split, width, height - split)

    # 5. Run the partitioning algorithm

    partition(spaces, 0, 0, building_width, building_height)

    # 6. Return the result

    return {
        "seed": seed,
        "building_width": building_width,
        "building_height": building_height,
        "rooms": layout
    }
