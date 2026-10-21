# Empezamos importando las librerías que voy a usar: Enum y Yyping vienen con Python; Pydantic es la que he instalado antes con pip install. 
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

# Enum es un tipo de dato especial que define un conjunto fijo de constantes con nombre. Es decir, para la clase que acabo de crear RequirementLevel, solo va a poder adquirir estos tres valores de string. La clase será por ejemplo: RequirementLevel.high y generará el valor high. 
class RequirementLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    
class RelationshipType(str, Enum):
    adjacent = "adjacent"
    near = "near"
    separate = "separate"
    
# Ahora empezamos a trabajar con Pydantic. Empezamos creando la clase Space, que va a heredar las características que vienen de BaseModel con pydantic.
class Space(BaseModel):
    id: str = Field(
        description="Short unique identifier, for example 'workspace' or 'meeting_room_1'"
    )

    name: str = Field(
        description="Human-readable name of the space"
    )

    target_area_m2: float = Field(
        gt=0,
        description="Desired area of the space in square metres"
    )

    min_area_m2: Optional[float] = Field(
        default=None,
        gt=0,
        description="Minimum acceptable area, if explicitly specified"
    )

    max_area_m2: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum acceptable area, if explicitly specified"
    )

    daylight: RequirementLevel = Field(
        default=RequirementLevel.medium,
        description="Relative requirement for access to natural light"
    )

    privacy: RequirementLevel = Field(
        default=RequirementLevel.medium,
        description="Relative privacy requirement"
    )

# Categoría añadida por mi en cuanto a la conexión con el exterior. Quizás lo de Optional no funciona. 
    outter_connection: Optional[RelationshipType] = Field(
        default=RelationshipType.near,
        description="Connection to the exterior world preference"
    )

# Ahora con la clase de Relationship. Para definir los objetos que se van a usar para indicar relaciones entre espacios.
class Relationship(BaseModel):

    space_a: str = Field(
        description="ID of the first space"
    )

    space_b: str = Field(
        description="ID of the second space"
    )

    type: RelationshipType = Field(
        description="Desired spatial relationship between the two spaces"
    )

    priority: int = Field(
        default=2,
        ge=1,
        le=3,
        description="Importance of this relationship: 1 low, 2 medium, 3 high"
    )
    
  # Y ahora creamos la clase para el objeto proyecto, que determinará aspectos generales sobre el edificio en su conjunto. 
class Project(BaseModel):
    name: str

    building_type: str

    total_area_m2: float = Field(
        gt=0,
        description="Approximate target total area"
    )

    occupants: Optional[int] = Field(
        default=None,
        ge=1
    )

    floors: int = Field(
        default=1,
        ge=1
    )

    spaces: list[Space]

    relationships: list[Relationship]



    
    
    
    
    
    
    
    
    
    