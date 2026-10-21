from dotenv import load_dotenv
from openai import OpenAI

from schema import Project
# Estoy importando la clase Project desde el archivo schema.py. 

load_dotenv()

client = OpenAI()

with open("data/brief.txt", "r", encoding="utf-8") as file:
    brief = file.read()


response = client.responses.parse(
    model="gpt-5.6-luna",

    input=[
        {
            "role": "system",
            "content": """
You extract architectural programmes from design briefs.

Convert the user's brief into the provided Project structure.

Rules:
- Use short, unique snake_case IDs for spaces.
- All relationships must reference those exact IDs.
- Infer reasonable target areas when the brief does not specify them.
- Do not invent unnecessary spaces.
- Use spatial relationships only when they are stated or strongly implied.
"""
        },
        {
            "role": "user",
            "content": brief
        }
    ],

    text_format=Project
)

project = response.output_parsed 

print(project.model_dump_json(indent=2))


from pathlib import Path

# Save the generated project as JSON
output_path = Path("data/programme.json")

output_path.write_text(
    project.model_dump_json(indent=2),
    encoding="utf-8"
)

# Check the total area
spaces_area = sum(space.target_area_m2 for space in project.spaces)

area_difference = project.total_area_m2 - spaces_area

print(f"Project target area: {project.total_area_m2} m²")
print(f"Total spaces area: {spaces_area} m²")
print(f"Area difference: {area_difference} m²")

print(f"Project saved to: {output_path}")