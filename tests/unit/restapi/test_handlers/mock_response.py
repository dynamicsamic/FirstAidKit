from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.domain.models import Medication


class MedicationProducer(BaseModel):
    name: str
    pk: Annotated[int, Field(alias="producerId")]


class MedicationCategory(BaseModel):
    name: str
    pk: Annotated[int, Field(alias="categoryId")]


class OutputMedication(Medication):
    model_config = ConfigDict(alias_generator=to_camel)
    pk: Annotated[int, Field(alias="medicationId")]
    producer: MedicationProducer | None = None
    category: MedicationCategory | None = None
