from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, Field, model_validator

from .constraints import (
    AIDKIT_LOCATION_LENTH,
    AIDKIT_NAME_LENGTH,
    CATEGORY_NAME_LENGTH,
    MEDICATION_BRAND_NAME_LENGTH,
    MEDICATION_GENERIC_NAME_LENGTH,
    PRODUCER_NAME_LENGTH,
)
from .types import DosageForm, MeasureUnit, PositiveInt


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


class BriefProducer(CreateProducer):
    producer_id: Annotated[PositiveInt, Field(alias="pk")]


class BriefCategory(CreateCategory):
    category_id: Annotated[PositiveInt, Field(alias="pk")]


class MedicationBase(BaseModel):
    brand_name: Annotated[str, Field(max_length=MEDICATION_BRAND_NAME_LENGTH)]
    generic_name: Annotated[str, Field(max_length=MEDICATION_GENERIC_NAME_LENGTH)]
    dosage_form: DosageForm


class CreateMedication(MedicationBase):
    producer_id: PositiveInt | None = None
    category_id: PositiveInt | None = None


class Medication(MedicationBase, PkDatetimeAttrsMixin):
    producer: BriefProducer | None = None
    category: BriefCategory | None = None


class PatchMedication(BaseModel, NonEmptyUpdateMixin):
    brand_name: (
        Annotated[str, Field(max_length=MEDICATION_BRAND_NAME_LENGTH)] | None
    ) = None
    generic_name: (
        Annotated[str, Field(max_length=MEDICATION_GENERIC_NAME_LENGTH)] | None
    ) = None
    dosage_form: DosageForm | None = None
    producer_id: PositiveInt | None = None
    category_id: PositiveInt | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreateMedicationStock(BaseModel):
    quantity: PositiveInt
    measure_unit: MeasureUnit
    production_date: date
    best_before: date
    opened_at: date | None = None

    medication_id: PositiveInt
    aidkit_id: PositiveInt


class MedicationStock(CreateMedication, PkDatetimeAttrsMixin):
    pass


class PatchMedicationStock(BaseModel, NonEmptyUpdateMixin):
    quantity: PositiveInt | None = None
    measure_unit: MeasureUnit | None = None
    production_date: date | None = None
    best_before: date | None = None
    opened_at: date | None = None

    medication_id: PositiveInt | None = None
    aidkit_id: PositiveInt | None = None


class CreateAidKit(BaseModel):
    name: Annotated[str, Field(max_length=AIDKIT_NAME_LENGTH)]
    location: Annotated[str, Field(max_length=AIDKIT_LOCATION_LENTH)] | None = None


class AidKit(CreateAidKit, PkDatetimeAttrsMixin):
    medications: list[MedicationStock] | None = None


class PatchAidKit(BaseModel, NonEmptyUpdateMixin):
    name: Annotated[str, Field(max_length=AIDKIT_NAME_LENGTH)] | None
    location: Annotated[str, Field(max_length=AIDKIT_LOCATION_LENTH)] | None = None
