from datetime import datetime
from typing import Generator

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from domain.types import DosageForm
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

    # producer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(250), unique=True)
    # meds: Mapped[list["Medication"]] = relationship(back_populates="producer", lazy="noload")
    meds: Mapped[Generator["Medication", None, None]] = relationship(
        back_populates="producer", lazy="noload"
    )


class Category(BaseModel):
    __tablename__ = "categories"

    # category_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    meds: Mapped[Generator["Medication", None, None]] = relationship(
        back_populates="category", lazy="noload"
    )


class Medication(BaseModel):
    __tablename__ = "medications"

    # medication_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand_name: Mapped[str] = mapped_column(String(250))
    generic_name: Mapped[str] = mapped_column(String(120))
    dosage_form: Mapped[Enum] = mapped_column(
        Enum(DosageForm, create_constraint=True, validate_string=True)
    )
    producer_id: Mapped[int] = mapped_column(
        ForeignKey(Producer.pk, ondelete="SET NULL")
    )  # refactor later
    producer: Mapped[Producer] = relationship(back_populates="meds", lazy="noload")
    category_id: Mapped[int] = mapped_column(
        ForeignKey(Category.pk, ondelete="SET NULL")
    )  # refactor later
    category: Mapped[Category] = relationship(back_populates="meds", lazy="noload")
    UniqueConstraint(brand_name, dosage_form, producer_id)
