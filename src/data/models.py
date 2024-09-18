from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    column_property,
    mapped_column,
    relationship,
)

from src.domain.constraints import (
    AIDKIT_LOCATION_LENTH,
    AIDKIT_NAME_LENGTH,
    CATEGORY_NAME_LENGTH,
    MEDICATION_BRAND_NAME_LENGTH,
    MEDICATION_GENERIC_NAME_LENGTH,
    PRODUCER_NAME_LENGTH,
)
from src.domain.types import DosageForm, MeasureUnit
from src.utils import now


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    __abstract__ = True

    pk: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, onupdate=now
    )


class Producer(BaseModel):
    __tablename__ = "producers"

    name: Mapped[str] = mapped_column(String(PRODUCER_NAME_LENGTH), unique=True)
    meds: Mapped[list["Medication"]] = relationship(
        back_populates="producer", lazy="noload"
    )


class Category(BaseModel):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(CATEGORY_NAME_LENGTH), unique=True)
    meds: Mapped[list["Medication"]] = relationship(
        back_populates="category", lazy="noload"
    )


class Medication(BaseModel):
    __tablename__ = "medications"

    brand_name: Mapped[str] = mapped_column(String(MEDICATION_BRAND_NAME_LENGTH))
    generic_name: Mapped[str] = mapped_column(String(MEDICATION_GENERIC_NAME_LENGTH))
    dosage_form: Mapped[Enum] = mapped_column(
        Enum(DosageForm, create_constraint=True, validate_string=True)
    )

    # Relations
    producer_id: Mapped[int] = mapped_column(
        ForeignKey(Producer.pk, ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey(Category.pk, ondelete="SET NULL"), nullable=True
    )

    producer: Mapped[Producer] = relationship(back_populates="meds", lazy="noload")
    category: Mapped[Category] = relationship(back_populates="meds", lazy="noload")
    stocks: Mapped[list["MedicationStock"]] = relationship(
        back_populates="medication",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Constraints
    UniqueConstraint(brand_name, dosage_form, producer_id)


class MedicationStock(BaseModel):
    __tablename__ = "stocks"

    quantity: Mapped[int]
    measure_unit: Mapped[Enum] = mapped_column(
        Enum(MeasureUnit, create_constraint=True, validate_string=True)
    )
    production_date: Mapped[date]
    best_before: Mapped[date]
    opened_at: Mapped[Optional[date]]

    # Relations
    medication_id: Mapped[int] = mapped_column(
        ForeignKey(Medication.pk, ondelete="CASCADE")
    )
    aidkit_id: Mapped[int] = mapped_column(ForeignKey("aidkits.pk", ondelete="CASCADE"))

    medication: Mapped[Medication] = relationship(
        back_populates="stocks", lazy="noload"
    )
    aidkit: Mapped["AidKit"] = relationship(back_populates="stocks", lazy="noload")


class AidKit(BaseModel):
    __tablename__ = "aidkits"

    pk: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(length=AIDKIT_NAME_LENGTH), unique=True)
    location: Mapped[str] = mapped_column(
        String(length=AIDKIT_LOCATION_LENTH), nullable=True
    )

    # Computed field.
    # Adds SELECT count(stocks.id) FROM stocks WHERE stocks.aidkit_id = aidkit.pk
    # to SELECT aidkit query.
    stock_count: Mapped[int] = column_property(
        select(func.count(MedicationStock.pk))
        .where(MedicationStock.aidkit_id == pk)
        .correlate_except(MedicationStock)
        .scalar_subquery()
    )

    # Relations
    stocks: Mapped[list[MedicationStock]] = relationship(
        back_populates="aidkit",
        lazy="noload",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
