from enum import StrEnum
from typing import Annotated

from pydantic import Field


class MeasureUnit(StrEnum):
    MILLIGRAM = "mg"
    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITERS = "ml"


class DosageForm(StrEnum):
    TABLET = "tablet"


PositiveInt = Annotated[int, Field(gt=0)]
PositiveFloat = Annotated[float, Field(gt=0.000)]
