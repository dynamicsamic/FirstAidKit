from typing import Any, Callable

from pydantic.alias_generators import to_snake
from sqlalchemy import insert

from src.data.models import Category, Medication, Producer
from src.domain.types import DosageForm

TEST_SAMPLE = 25

prod_vals = [{"name": f"Producer_{i}"} for i in range(1, TEST_SAMPLE)]
cat_vals = [{"name": f"Category_{i}"} for i in range(1, TEST_SAMPLE)]
med_vals = [
    {
        "brand_name": f"Test_{i}",
        "generic_name": f"Test_{i}",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
    }
    for i in range(1, TEST_SAMPLE)
]


async def populate_db(con):
    await con.execute(insert(Producer).values(prod_vals))
    await con.execute(insert(Category).values(cat_vals))
    await con.execute(insert(Medication).values(med_vals))
    await con.commit()


def convert_dict(converter: Callable[[str], str], replace_fields: dict[str, str]):
    "Convert a dictionary with provided converter and replace given fields."

    def convert(
        obj: dict[str, Any],
    ) -> dict:
        replaced = {new: obj.pop(old) for old, new in replace_fields.items()}
        converted = {converter(attr): val for attr, val in obj.items()}
        return converted | replaced

    return convert


convert_to_producer = convert_dict(to_snake, {"producerId": "pk"})
convert_to_category = convert_dict(to_snake, {"categoryId": "pk"})
