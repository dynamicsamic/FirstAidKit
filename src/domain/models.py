from datetime import date, datetime

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

from .types import DosageForm, MeasureUnit, PositiveFloat, PositiveInt


class BaseModel(_BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class MedicationCategory(BaseModel):
    category_id: PositiveInt
    name: str
    created_at: datetime
    updated_at: datetime

class MedicationProducer(BaseModel):
    producer_id: PositiveInt
    name: str
    created_at: datetime
    updated_at: datetime

class Medication(BaseModel):
    meds_id: PositiveInt
    brand_name: str
    generic_name: str
    dosage_form: DosageForm
    producer: str = MedicationProducer
    category: MedicationCategory
    created_at: datetime
    updated_at: datetime


class MedicationStock(BaseModel):
    medication_id: PositiveInt
    quantity: PositiveFloat
    measure_unit: MeasureUnit
    production_date: date
    best_before: date
    start_consuming_at: datetime| None = None


class CreateMedication(BaseModel):
    brand_name: str
    generic_name: str
    dosage_form: DosageForm
    producer: str = MedicationProducer
    category: MedicationCategory


"""
view all medications
add new medication
view one medication
update one medication
delete one medication

patch meds/1/update
post meds/1/refill
post meds/1/consume


"""
