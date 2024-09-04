from typing import Annotated

from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from src.domain.models import CreateProducer, Producer

producer_dto_config = DTOConfig(
    rename_fields={"pk": "producerId"}, rename_strategy="camel"
)
ProducerDTO = PydanticDTO[Annotated[Producer, producer_dto_config]]
CreateProducerDTO = PydanticDTO[CreateProducer]
