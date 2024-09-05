from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field, model_validator

from .constraints import CATEGORY_NAME_LENGTH, PRODUCER_NAME_LENGTH
from .types import DosageForm, MeasureUnit, PositiveFloat, PositiveInt


class NonEmptyUpdateMixin:
    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_non_empty_field(cls, data: dict[str, Any]) -> Any:
        if all(val is None for val in data.values()):
            raise ValueError("At least one field must contain a not None value")
        return data


class PkDatetimeAttrsMixin:
    pk: PositiveInt
    created_at: datetime
    updated_at: datetime


class BaseModel(_BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CreateCategory(BaseModel):
    name: Annotated[str, Field(max_length=CATEGORY_NAME_LENGTH)]


class Category(CreateCategory, PkDatetimeAttrsMixin):
    pass


class PatchCategory(BaseModel, NonEmptyUpdateMixin):
    name: Annotated[str, Field(max_length=CATEGORY_NAME_LENGTH)] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreateProducer(BaseModel):
    name: Annotated[str, Field(max_length=PRODUCER_NAME_LENGTH)]


class Producer(CreateProducer, PkDatetimeAttrsMixin):
    pass


class PatchProducer(BaseModel, NonEmptyUpdateMixin):
    name: Annotated[str, Field(max_length=PRODUCER_NAME_LENGTH)] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Medication(BaseModel):
    meds_id: PositiveInt
    brand_name: str
    generic_name: str
    dosage_form: DosageForm
    producer: str = Producer
    category: Category
    created_at: datetime
    updated_at: datetime


class MedicationStock(BaseModel):
    medication_id: PositiveInt
    quantity: PositiveFloat
    measure_unit: MeasureUnit
    production_date: date
    best_before: date
    start_consuming_at: datetime | None = None


class CreateMedication(BaseModel):
    brand_name: str
    generic_name: str
    dosage_form: DosageForm
    producer: str = Producer
    category: Category
