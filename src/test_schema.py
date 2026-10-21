#Importamos las clases desde el otro archivo. En este documento estamos trabajando ya en el mismo environment. 
from schema import (
    Project,
    Space,
    Relationship,
    RequirementLevel,
    RelationshipType,
)

### ---------------

kitchen_01 = Space(
  id="kitchen",
  name="Shared Kitchen",
  target_area_m2=60,
  min_area_m2=20,
  daylight=RequirementLevel.high,
  outter_connection=RelationshipType.adjacent,
  privacy=RequirementLevel.low
  )
      
print(kitchen_01)

    
############

project = Project(
    name="Architecture Office",
    building_type="office",
    total_area_m2=140,
    occupants=12,

    spaces=[
        Space(
            id="workspace",
            name="Open Workspace",
            target_area_m2=60,
            daylight="high",
            privacy="low"
        ),

        Space(
            id="kitchen",
            name="Kitchen",
            target_area_m2=12,
            daylight="medium",
            privacy="low"
        )
    ],

    relationships=[
        Relationship(
            space_a="workspace",
            space_b="kitchen",
            type="adjacent",
            priority=3
        )
    ]
)

print("And now the JSON:")

print(project.model_dump_json(indent=2))