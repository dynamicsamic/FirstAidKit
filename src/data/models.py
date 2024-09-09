from datetime import datetime
from typing import Generator

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.domain.constraints import (
    CATEGORY_NAME_LENGTH,
    MEDICATION_BRAND_NAME_LENGTH,
    MEDICATION_GENERIC_NAME_LENGTH,
    PRODUCER_NAME_LENGTH,
)
from src.domain.types import DosageForm
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
    # meds: Mapped[list["Medication"]] = relationship(back_populates="producer", lazy="noload")
    meds: Mapped[Generator["Medication", None, None]] = relationship(
        back_populates="producer", lazy="noload"
    )


class Category(BaseModel):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(CATEGORY_NAME_LENGTH), unique=True)
    meds: Mapped[Generator["Medication", None, None]] = relationship(
        back_populates="category", lazy="noload"
    )


class Medication(BaseModel):
    __tablename__ = "medications"

    brand_name: Mapped[str] = mapped_column(String(MEDICATION_BRAND_NAME_LENGTH))
    generic_name: Mapped[str] = mapped_column(String(MEDICATION_GENERIC_NAME_LENGTH))
    dosage_form: Mapped[Enum] = mapped_column(
        Enum(DosageForm, create_constraint=True, validate_string=True)
    )
    producer_id: Mapped[int] = mapped_column(
        ForeignKey(Producer.pk, ondelete="SET NULL"), nullable=True
    )  # refactor later
    producer: Mapped[Producer] = relationship(back_populates="meds", lazy="noload")
    category_id: Mapped[int] = mapped_column(
        ForeignKey(Category.pk, ondelete="SET NULL"), nullable=True
    )  # refactor later
    category: Mapped[Category] = relationship(back_populates="meds", lazy="noload")
    UniqueConstraint(brand_name, dosage_form, producer_id)
