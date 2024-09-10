from typing import Any

from pydantic import BaseModel


class MockProducer(BaseModel):
    name: Any = None
    extra: Any = None
    created_at: Any = None
    updated_at: Any = None

class MockCategory(MockProducer):
    pass

class MockMedication(MockProducer):
    brand_name: Any = None
    generic_name: Any = None
    dosage_form: Any = None
    producer_id: Any = None
    category_id: Any = None