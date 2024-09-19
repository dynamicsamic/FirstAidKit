from typing import Annotated

from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from src.domain.models import (
    AidKit,
    Category,
    CreateAidKit,
    CreateCategory,
    CreateMedication,
    CreateProducer,
    Medication,
    PatchAidKit,
    PatchCategory,
    PatchMedication,
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

MedicationDTO = PydanticDTO[
    Annotated[
        Medication,
        DTOConfig(
            rename_fields={
                "pk": "medicationId",
                "medication_producer__pk": "producerId",
            },
            rename_strategy="camel",
        ),
    ]
]
CreateMedicationDTO = PydanticDTO[CreateMedication]
PatchMedicationDTO = PydanticDTO[
    Annotated[
        PatchMedication,
        DTOConfig(forbid_unknown_fields=True),
    ]
]

AidKitDTO = PydanticDTO[
    Annotated[
        AidKit,
        DTOConfig(rename_fields={"pk": "aidKitId"}, rename_strategy="camel"),
    ]
]
CreateAidKitDTO = PydanticDTO[CreateAidKit]
PatchAidKitDTO = PydanticDTO[
    Annotated[PatchAidKit, DTOConfig(forbid_unknown_fields=True)]
]
