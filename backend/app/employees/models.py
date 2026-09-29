from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint("length(trim(employee_code)) > 0", name="ck_employees_employee_code_nonempty"),
        CheckConstraint("length(trim(first_name)) > 0", name="ck_employees_first_name_nonempty"),
        CheckConstraint("length(trim(last_name)) > 0", name="ck_employees_last_name_nonempty"),
        CheckConstraint("length(trim(email)) > 0", name="ck_employees_email_nonempty"),
        CheckConstraint(
            "length(country) = 2 AND country = upper(country) "
            "AND substr(country, 1, 1) BETWEEN 'A' AND 'Z' "
            "AND substr(country, 2, 1) BETWEEN 'A' AND 'Z'",
            name="ck_employees_country_alpha2",
        ),
        CheckConstraint("length(trim(department)) > 0", name="ck_employees_department_nonempty"),
        CheckConstraint("length(trim(job_title)) > 0", name="ck_employees_job_title_nonempty"),
        UniqueConstraint("employee_code", name="uq_employees_employee_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


Index("uq_employees_email", func.lower(Employee.email), unique=True)
