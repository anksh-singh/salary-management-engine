"""Create the employees table.

Revision ID: c12f6ae9312a
Revises:
Create Date: 2026-09-28
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c12f6ae9312a"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("employee_code", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=False),
        sa.Column("job_title", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(trim(employee_code)) > 0", name="ck_employees_employee_code_nonempty"),
        sa.CheckConstraint("length(trim(first_name)) > 0", name="ck_employees_first_name_nonempty"),
        sa.CheckConstraint("length(trim(last_name)) > 0", name="ck_employees_last_name_nonempty"),
        sa.CheckConstraint("length(trim(email)) > 0", name="ck_employees_email_nonempty"),
        sa.CheckConstraint(
            "length(country) = 2 AND country = upper(country) "
            "AND substr(country, 1, 1) BETWEEN 'A' AND 'Z' "
            "AND substr(country, 2, 1) BETWEEN 'A' AND 'Z'",
            name="ck_employees_country_alpha2",
        ),
        sa.CheckConstraint("length(trim(department)) > 0", name="ck_employees_department_nonempty"),
        sa.CheckConstraint("length(trim(job_title)) > 0", name="ck_employees_job_title_nonempty"),
        sa.PrimaryKeyConstraint("id", name="pk_employees"),
        sa.UniqueConstraint("employee_code", name="uq_employees_employee_code"),
    )
    op.create_index("uq_employees_email", "employees", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_employees_email", table_name="employees")
    op.drop_table("employees")
