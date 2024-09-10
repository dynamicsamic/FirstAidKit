from typing import Any

from pydantic import BaseModel


class MockProducer(BaseModel):
    name: Any = None
    extra: Any = None
    created_at: Any = None
    updated_at: Any = None

class MockCategory(MockProducer):
    pass