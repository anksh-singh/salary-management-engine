from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Compensation(Base):
    __tablename__ = "compensations"
    __table_args__ = (
        PrimaryKeyConstraint("employee_id", name="pk_compensations"),
        ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_compensations_employee_id_employees",
        ),
        CheckConstraint(
            "amount > 0 AND amount <> 'NaN'",
            name="ck_compensations_amount_positive",
        ),
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency) "
            "AND substr(currency, 1, 1) BETWEEN 'A' AND 'Z' "
            "AND substr(currency, 2, 1) BETWEEN 'A' AND 'Z' "
            "AND substr(currency, 3, 1) BETWEEN 'A' AND 'Z'",
            name="ck_compensations_currency_alpha3",
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
