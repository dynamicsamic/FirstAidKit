from typing import Annotated

from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from src.domain.models import (
    Category,
    CreateCategory,
    CreateProducer,
    PatchCategory,
    PatchProducer,
    Producer,
)

ProducerDTO = PydanticDTO[
    Annotated[
        Producer,
        DTOConfig(rename_fields={"pk": "producerId"}, rename_strategy="camel"),
    ]
]
CreateProducerDTO = PydanticDTO[CreateProducer]
PatchProducerDTO = PydanticDTO[
    Annotated[PatchProducer, DTOConfig(forbid_unknown_fields=True)]
]

CategoryDTO = PydanticDTO[
    Annotated[
        Category,
        DTOConfig(rename_fields={"pk": "categoryId"}, rename_strategy="camel"),
    ]
]
CreateCategoryDTO = PydanticDTO[CreateCategory]
PatchCategoryDTO = PydanticDTO[
    Annotated[
        PatchCategory,
        DTOConfig(forbid_unknown_fields=True),
    ]
]
