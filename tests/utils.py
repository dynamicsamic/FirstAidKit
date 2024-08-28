from sqlalchemy import insert

from src.data.models import Category, Medication, Producer
from src.domain.types import DosageForm

prod_vals = [{"name": f"Producer_{i}"} for i in range(1, 10)]
cat_vals = [{"name": f"Category_{i}"} for i in range(1, 10)]
med_vals = [
    {
        "brand_name": f"Test_{i}",
        "generic_name": f"Test_{i}",
        "dosage_form": DosageForm.TABLET,
        "producer_id": 1,
        "category_id": 1,
    }
    for i in range(1, 10)
]

async def populate_db(con):
    await con.execute(insert(Producer).values(prod_vals))
    await con.execute(insert(Category).values(cat_vals))
    await con.execute(insert(Medication).values(med_vals))
    await con.commit()
