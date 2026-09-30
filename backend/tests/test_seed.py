from collections.abc import Iterator
from decimal import Decimal
import re

from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.compensation.models import Compensation
from app.database import Base
from app.employees.models import Employee
from app.seed import SEED_EMPLOYEE_COUNT, generate_seed_data, seed_database


def test_default_seed_data_is_deterministic_and_contains_ten_thousand_employees() -> None:
    employees, compensations = generate_seed_data()
    repeated_employees, repeated_compensations = generate_seed_data()

    assert len(employees) == SEED_EMPLOYEE_COUNT == 10_000
    assert employees == repeated_employees
    assert compensations == repeated_compensations
    assert all(employee["created_at"] == employee["updated_at"] for employee in employees)


def test_generated_seed_data_has_valid_unique_fields_and_realistic_distributions() -> None:
    employees, compensations = generate_seed_data()
    employee_codes = [employee["employee_code"] for employee in employees]
    emails = [employee["email"] for employee in employees]
    employee_ids = {employee["id"] for employee in employees}
    compensation_rows = [row for row in compensations if row is not None]

    assert len(set(employee_codes)) == SEED_EMPLOYEE_COUNT
    assert len(set(emails)) == SEED_EMPLOYEE_COUNT
    assert all(employee["first_name"] and employee["last_name"] for employee in employees)
    assert all(re.fullmatch(r"[A-Z]{2}", employee["country"]) for employee in employees)
    assert all(employee["department"] and employee["job_title"] for employee in employees)
    assert len({employee["country"] for employee in employees}) > 5
    assert len({employee["department"] for employee in employees}) > 5
    assert len({employee["job_title"] for employee in employees}) > 10
    assert len({row["currency"] for row in compensation_rows}) > 5
    assert len(compensation_rows) == 9_500
    assert all(row["employee_id"] in employee_ids for row in compensation_rows)
    assert all(
        isinstance(row["amount"], Decimal)
        and row["amount"] > 0
        and max(0, -row["amount"].as_tuple().exponent) <= 3
        for row in compensation_rows
    )


def test_seed_replaces_existing_data_and_is_repeatable() -> None:
    engine: Engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    try:
        with Session(engine) as session:
            old_employee = Employee(
                employee_code="OLD-001",
                first_name="Old",
                last_name="Record",
                email="old@example.test",
                country="US",
                department="Legacy",
                job_title="Legacy Role",
            )
            session.add(old_employee)
            session.flush()
            session.add(
                Compensation(employee_id=old_employee.id, amount=Decimal("1"), currency="USD")
            )
            session.commit()

        first_result = seed_database(session_factory, employee_count=41, batch_size=7)
        with Session(engine) as session:
            first_codes = session.scalars(select(Employee.employee_code).order_by(Employee.employee_code)).all()
            first_compensation_count = session.scalar(select(func.count()).select_from(Compensation))

        second_result = seed_database(session_factory, employee_count=41, batch_size=7)
        with Session(engine) as session:
            second_codes = session.scalars(select(Employee.employee_code).order_by(Employee.employee_code)).all()
            employee_count = session.scalar(select(func.count()).select_from(Employee))
            compensation_count = session.scalar(select(func.count()).select_from(Compensation))

        assert first_result == second_result == (41, 39)
        assert first_codes == second_codes
        assert employee_count == 41
        assert compensation_count == first_compensation_count == 39
        assert "OLD-001" not in second_codes
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
