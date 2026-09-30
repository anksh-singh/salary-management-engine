"""Create current employee compensations.

Revision ID: a91c04d68b7e
Revises: c12f6ae9312a
Create Date: 2026-09-30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a91c04d68b7e"
down_revision: str | None = "c12f6ae9312a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "compensations",
        sa.Column("employee_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=3), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "amount > 0 AND amount <> 'NaN'",
            name="ck_compensations_amount_positive",
        ),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency) "
            "AND substr(currency, 1, 1) BETWEEN 'A' AND 'Z' "
            "AND substr(currency, 2, 1) BETWEEN 'A' AND 'Z' "
            "AND substr(currency, 3, 1) BETWEEN 'A' AND 'Z'",
            name="ck_compensations_currency_alpha3",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_compensations_employee_id_employees",
        ),
        sa.PrimaryKeyConstraint("employee_id", name="pk_compensations"),
    )


def downgrade() -> None:
    op.drop_table("compensations")
