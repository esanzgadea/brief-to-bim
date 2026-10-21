from pathlib import Path
from schema import Project
import networkx as nx

# Read our existing JSON
json_text = Path("data/programme.json").read_text(encoding="utf-8")

project = Project.model_validate_json(json_text)

# Create an empty graph
graph = nx.Graph()

for space in project.spaces:
    graph.add_node(
        space.id,
        name=space.name,
        area=space.target_area_m2,
        daylight=space.daylight.value,
        privacy=space.privacy.value
    )


for relationship in project.relationships:
    graph.add_edge(
        relationship.space_a,
        relationship.space_b,
        type=relationship.type.value,
        priority=relationship.priority
    )


print(graph)

print("\nNODES:")
for node, attributes in graph.nodes(data=True):
    print(node, attributes)

print("\nEDGES:")
for space_a, space_b, attributes in graph.edges(data=True):
    print(space_a, "<->", space_b, attributes)

#----------Generate the graph-----------------------------

import matplotlib.pyplot as plt
from pathlib import Path
import textwrap

# 1. Define node colours according to daylight requirements

daylight_colors = {
    "high": "#F4D58D",
    "medium": "#BFD7EA",
    "low": "#D8DADF"
}

node_colors = [
    daylight_colors[data["daylight"]]
    for node, data in graph.nodes(data=True)
]

# 2. Define node sizes according to room areas

node_sizes = [
    950 + data["area"] * 32
    for node, data in graph.nodes(data=True)
]

# 3. Define node labels

labels = {}

for node, data in graph.nodes(data=True):
    name = textwrap.fill(data["name"], width=11)
    area = data["area"]
    labels[node] = f"{name}\n{area:g} m²"

# 4. Calculate node positions

positions = nx.spring_layout(graph, seed=42)

# 5. Create the figure

fig, ax = plt.subplots(figsize=(12, 8))

# 6. Draw relationships using different line styles

edge_styles = {
    "adjacent": ("solid", "#238B83"),
    "near": ("dashed", "#8492A5"),
    "separate": ("dotted", "#C45B5B")
}

for relationship_type, (style, color) in edge_styles.items():

    edges = [
        (a, b)
        for a, b, data in graph.edges(data=True)
        if data["type"] == relationship_type
    ]

    nx.draw_networkx_edges(
        graph,
        positions,
        edgelist=edges,
        style=style,
        edge_color=color,
        width=2.5,
        ax=ax
    )

# 7. Draw nodes

nx.draw_networkx_nodes(
    graph,
    positions,
    node_size=node_sizes,
    node_color=node_colors,
    edgecolors="#465466",
    linewidths=1.2,
    ax=ax
)

# 8. Draw labels

nx.draw_networkx_labels(
    graph,
    positions,
    labels=labels,
    font_size=8,
    font_weight="medium",
    ax=ax
)

# 9. Format and export

ax.set_title("Architectural Programme — Spatial Graph", fontsize=16)
ax.axis("off")

Path("outputs").mkdir(exist_ok=True)

plt.savefig(
    "outputs/spatial_graph.png",
    dpi=250,
    bbox_inches="tight",
    facecolor="white"
)

plt.show()